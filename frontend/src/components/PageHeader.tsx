type Props = {
  title: string
  subtitle: string
}

function PageHeader({ title, subtitle }: Props) {
  return (
    <header className="page-header">
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </header>
  )
}

export default PageHeader