type PageHeaderProps = {
  title: string;
  description: string;
  eyebrow?: string;
};

export function PageHeader({
  title,
  description,
  eyebrow = "MVP workflow",
}: PageHeaderProps) {
  return (
    <header className="surface-section">
      <p className="section-eyebrow">{eyebrow}</p>
      <h2 className="section-title">{title}</h2>
      <p className="body-copy">{description}</p>
    </header>
  );
}
