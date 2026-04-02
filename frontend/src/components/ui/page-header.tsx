type PageHeaderProps = {
  title: string;
  description: string;
  eyebrow?: string;
  compact?: boolean;
};

export function PageHeader({
  title,
  description,
  eyebrow = "GrantPath AI",
  compact = false,
}: PageHeaderProps) {
  return (
    <header className={compact ? "section-header section-header--compact" : "section-header"}>
      <p className="section-eyebrow">{eyebrow}</p>
      <h2 className="section-title">{title}</h2>
      <p className="body-copy">{description}</p>
    </header>
  );
}
