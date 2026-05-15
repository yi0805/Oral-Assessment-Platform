/* global AudioWorkletProcessor, sampleRate, registerProcessor */
//
// AudioWorklet that downsamples the microphone input to 16 kHz mono
// signed-16-bit little-endian PCM and posts the resulting frames back
// to the main thread.
//
// Issue #72. Loaded by useAudioContext (added in the next commit) via
//
//     await audioCtx.audioWorklet.addModule("/stt-pcm-worklet.js");
//     new AudioWorkletNode(audioCtx, "stt-pcm-processor");
//
// Lives in public/ rather than src/ because AudioWorklets execute in a
// separate AudioWorkletGlobalScope that doesn't share Vite's module
// graph — the file must be served as a top-level static asset that the
// main thread can fetch via the path above.
//
// Target format rationale:
//   * 16 kHz mono — what AWS Transcribe Streaming wants with
//     media_encoding="pcm", and the recommended rate for English speech
//     models. Higher rates buy nothing for voice transcription.
//   * Int16 little-endian — the wire format expected by the streaming
//     SDK's send_audio_event(audio_chunk=…) parameter.
//
// Resampling uses linear interpolation, which is adequate for voice
// (sub-4 kHz dominant content) and is dramatically simpler than a
// proper polyphase filter. Anti-alias filtering would matter for music
// but not for speech.

// 16 kHz mono Int16 — the format AWS Transcribe Streaming expects.
const TARGET_SAMPLE_RATE = 16000;

// Batch ~100 ms of audio per postMessage call (1600 samples / 3200
// bytes at 16 kHz mono Int16). The AudioWorklet process() callback
// fires every 128 frames; without batching we would spam the main
// thread with ~370 messages per second on a 48 kHz context.
const FRAMES_PER_POST = 1600;

class STTPCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super();

    // Tail samples carried over from the previous quantum so the
    // resampler can interpolate across quantum boundaries without
    // dropping the last sample of each chunk.
    this._inputTail = new Float32Array(0);

    // Fractional read position into the (tail + new-input) combined
    // buffer at the start of each quantum. Roughly equivalent to
    // "where we left off in the source signal".
    this._resamplePos = 0;

    // Output buffer that fills up with downsampled Int16 samples and
    // flushes to the main thread once it reaches FRAMES_PER_POST.
    this._outBuffer = new Int16Array(FRAMES_PER_POST);
    this._outIndex = 0;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || input.length === 0) {
      // Mic not yet streaming (e.g. paused track). Keep the processor
      // alive but produce nothing.
      return true;
    }

    // ----- 1. Mix down to mono -----
    const channelCount = input.length;
    const frameCount = input[0].length;
    let mono;
    if (channelCount === 1) {
      mono = input[0];
    } else {
      mono = new Float32Array(frameCount);
      for (let i = 0; i < frameCount; i++) {
        let sum = 0;
        for (let c = 0; c < channelCount; c++) {
          sum += input[c][i];
        }
        mono[i] = sum / channelCount;
      }
    }

    // ----- 2. Concatenate tail + new audio for cross-quantum resample -----
    const combined = new Float32Array(this._inputTail.length + mono.length);
    combined.set(this._inputTail, 0);
    combined.set(mono, this._inputTail.length);

    // ----- 3. Linear-interpolation resample to TARGET_SAMPLE_RATE -----
    const ratio = sampleRate / TARGET_SAMPLE_RATE;
    let readPos = this._resamplePos;

    while (Math.floor(readPos) + 1 < combined.length) {
      const floorIdx = Math.floor(readPos);
      const frac = readPos - floorIdx;
      const sample =
        combined[floorIdx] * (1 - frac) + combined[floorIdx + 1] * frac;

      // Float32 [-1, 1] → Int16 [-32768, 32767]. Clamp first — mic
      // samples occasionally exceed nominal range. The asymmetric scale
      // (0x8000 vs 0x7fff) matches the canonical PCM mapping.
      let s = sample;
      if (s > 1) s = 1;
      else if (s < -1) s = -1;
      this._outBuffer[this._outIndex++] = s < 0 ? s * 0x8000 : s * 0x7fff;

      if (this._outIndex >= FRAMES_PER_POST) {
        // Transfer buffer ownership to the main thread (zero-copy).
        const transfer = this._outBuffer.buffer;
        this.port.postMessage(transfer, [transfer]);
        // Allocate a fresh backing buffer for subsequent samples —
        // the previous one is now detached.
        this._outBuffer = new Int16Array(FRAMES_PER_POST);
        this._outIndex = 0;
      }

      readPos += ratio;
    }

    // ----- 4. Save the un-consumed tail + fractional offset -----
    // The clamp matters: when the resampler overshoots the end of the
    // combined buffer (tailStart > combined.length), we have no tail
    // to keep, but the next quantum's read position must remember that
    // overshoot — otherwise we silently re-align to a 0 offset every
    // chunk and produce ~0.78% extra samples at ratio=3.
    const tailStart = Math.floor(readPos);
    const tailKeepStart = Math.min(tailStart, combined.length);
    this._inputTail = combined.slice(tailKeepStart);
    this._resamplePos = readPos - tailKeepStart;

    // Returning true keeps the processor alive for the next quantum.
    return true;
  }
}

registerProcessor("stt-pcm-processor", STTPCMProcessor);
