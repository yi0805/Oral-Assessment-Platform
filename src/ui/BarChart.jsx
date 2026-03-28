import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
} from "recharts";

{/*npm install recharts to use this */}
function ScoreBarChart({ data }) {
    return (
        <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data}>
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false}/>
                {/* shows the exact count for each grade */ }
                <Tooltip />
                <Bar dataKey="students" fill="var(--color-primary)" />
            </BarChart>
        </ResponsiveContainer>
    );
}

export default ScoreBarChart; 