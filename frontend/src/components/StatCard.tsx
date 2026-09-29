type Props = {
  label: string
  value: string
}

function StatCard({ label, value }: Props) {
  return (
    <div className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

export default StatCard