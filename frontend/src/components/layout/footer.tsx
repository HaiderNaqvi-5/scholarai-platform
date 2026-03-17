import Link from "next/link";

export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="site-footer">
      <div className="page-shell">
        <div className="site-footer__inner">
          <div className="site-footer__brand">
            <Link className="brand-lockup brand-lockup--link" href="/">
              <span className="brand-mark" aria-hidden="true" />
              <span className="brand-lockup__text">
                <span className="brand-title">ScholarAI</span>
              </span>
            </Link>
          </div>
          <nav className="site-footer__links">
            <Link className="site-footer__link" href="/scholarships">
              Scholarships
            </Link>
            <Link className="site-footer__link" href="/#how-it-works">
              How it works
            </Link>
            <Link className="site-footer__link" href="/login">
              Sign in
            </Link>
          </nav>
          <p className="site-footer__copy">
            © {year} ScholarAI. A research project, not a commercial product.
          </p>
        </div>
      </div>
    </footer>
  );
}
