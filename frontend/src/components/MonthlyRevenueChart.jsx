import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

function MonthlyRevenueChart({ data }) {
  // Transform data for charting
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];

    // Group by year and sum monthly revenues
    const yearlyData = {};
    data.forEach((entry) => {
      const year = entry.year;
      if (!yearlyData[year]) {
        yearlyData[year] = {
          year,
          revenue: 0,
        };
      }
      yearlyData[year].revenue += entry.revenue;
    });

    // Convert to array and format
    return Object.values(yearlyData).map((item) => ({
      year: `Year ${item.year}`,
      revenue: item.revenue,
      revenueFormatted: new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(item.revenue),
    }));
  }, [data]);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="chart-tooltip">
          <p className="tooltip-label">{payload[0].payload.year}</p>
          <p className="tooltip-value">
            Revenue: {payload[0].payload.revenueFormatted}
          </p>
        </div>
      );
    }
    return null;
  };

  if (chartData.length === 0) {
    return <div>No revenue data available</div>;
  }

  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="year"
            angle={-45}
            textAnchor="end"
            height={100}
            interval={0}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            tickFormatter={(value) =>
              new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                notation: 'compact',
                maximumFractionDigits: 0,
              }).format(value)
            }
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Line
            type="monotone"
            dataKey="revenue"
            stroke="#3b82f6"
            strokeWidth={2}
            name="Annual Revenue"
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default MonthlyRevenueChart;
