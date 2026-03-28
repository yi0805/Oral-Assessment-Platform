import {
    BarChart,
    Bar,
    XAxis,
    Tooltip,
    ResponsiveContainer,
} from "recharts";
import { useMemo } from "react";

// npm install recharts to use this
// when scores are changed, recalculate data with usememo and update the chart
function ScoreBarChart({ scores }) {
    const chartData = useMemo(() => {
        // prevent crash by showing an empty graph when the input doesn't exsit
        if (!scores || !Array.isArray(scores)) return [];

        const gradeCounts = { A: 0, B: 0, C: 0, D: 0 };

        scores.forEach((item) => {
            const score = item.score;
            if (score >= 80) gradeCounts.A++;
            else if (score >= 70) gradeCounts.B++;
            else if (score >= 60) gradeCounts.C++;
            else gradeCounts.D++;
        });

        return [
            { name: "A", students: gradeCounts.A },
            { name: "B", students: gradeCounts.B },
            { name: "C", students: gradeCounts.C },
            { name: "D", students: gradeCounts.D },
        ];
    }, [scores]); 

    return (
        <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData}>
                <XAxis dataKey="name" />
                <Tooltip />
                <Bar
                    dataKey="students"
                    fill="var(--color-primary)"
                />
            </BarChart>
        </ResponsiveContainer>
    );
}

export default ScoreBarChart; 