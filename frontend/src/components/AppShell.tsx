import { useEffect, useRef, useState, type ReactNode } from "react";
import { getHealth } from "../api/health";
import { useApiResource } from "../hooks/useApiResource";
import { usePathname } from "../utils/navigation";
import { useProductCopy } from "../product/copy";
import { usePreferences } from "../product/preferences";
import { CommandPalette } from "../product/CommandPalette";
import { Link } from "./Link";
import { LanguageSelector } from "./LanguageSelector";

export function AppShell({ children }: { children: ReactNode }) {
  const copy = useProductCopy();
  const pathname = usePathname();
  const { preferences, update } = usePreferences();
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const sidebar = useRef<HTMLElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const closeMenu = () => {
    setMenuOpen(false);
    menuButton.current?.focus();
  };
  const health = useApiResource((signal) => getHealth(signal), []);
  const links = [
    { href: "/", label: copy.home, icon: "◫" },
    { href: "/strategies", label: copy.strategies, icon: "◇" },
    { href: "/experiments", label: copy.research, icon: "▤" },
    { href: "/paper", label: copy.accounts, icon: "▣" },
    { href: "/data", label: copy.data, icon: "▥" },
  ];
  const active = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);
  const location =
    links.find((item) => active(item.href))?.label ??
    (pathname.startsWith("/research/new")
      ? copy.newStudy
      : pathname.startsWith("/research")
        ? copy.archive
        : pathname === "/settings"
          ? copy.settings
          : pathname === "/help"
            ? copy.help
            : copy.legacy);
  useEffect(() => {
    if (menuOpen) sidebar.current?.querySelector("a")?.focus();
  }, [menuOpen]);
  useEffect(() => {
    document.getElementById("main-content")?.focus();
  }, [pathname]);
  useEffect(() => {
    document.documentElement.dataset.theme = preferences.theme;
    document.documentElement.dataset.motion = preferences.motion;
    document.documentElement.dataset.marketColors = preferences.marketColors;
  }, [preferences]);
  useEffect(() => {
    const handle = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearchOpen((open) => !open);
      }
      if (
        event.key === "Escape" &&
        sidebar.current?.classList.contains("sidebarOpen") &&
        sidebar.current?.contains(document.activeElement)
      )
        closeMenu();
    };
    window.addEventListener("keydown", handle);
    return () => window.removeEventListener("keydown", handle);
  }, []);
  return (
    <div className="appShell">
      <a className="skipLink" href="#main-content">
        {copy.skipContent}
      </a>
      <aside
        ref={sidebar}
        className={`sidebar ${menuOpen ? "sidebarOpen" : ""}`}
      >
        {menuOpen && (
          <button
            className="iconButton mobileMenu"
            onClick={closeMenu}
            aria-label={copy.close}
          >
            ×
          </button>
        )}
        <Link
          className="brand"
          href="/"
          aria-label={`QUANT ${copy.brand}`}
          onClick={() => setMenuOpen(false)}
        >
          <span className="brandMark">Q</span>
          <span>
            QUANT<span className="brandSubtitle">{copy.brand}</span>
          </span>
        </Link>
        <div className="sidebarScope">
          <span className="scopeMark">CN</span>
          <span>
            A-SHARE<span>{copy.simulation}</span>
          </span>
        </div>
        <nav aria-label={copy.navigation} onClick={() => setMenuOpen(false)}>
          {links.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active(item.href) ? "page" : undefined}
            >
              <span aria-hidden="true" className="navIcon">
                {item.icon}
              </span>
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="sidebarBottom">
          <nav aria-label={copy.help} onClick={() => setMenuOpen(false)}>
            <Link
              href="/help"
              aria-current={pathname === "/help" ? "page" : undefined}
            >
              <span className="navIcon" aria-hidden="true">
                ?
              </span>
              {copy.help}
            </Link>
            <Link
              href="/settings"
              aria-current={pathname === "/settings" ? "page" : undefined}
            >
              <span className="navIcon" aria-hidden="true">
                ⚙
              </span>
              {copy.settings}
            </Link>
          </nav>
          <span className="localLabel">{copy.local}</span>
        </div>
      </aside>
      {menuOpen && (
        <button
          className="sidebarBackdrop"
          aria-label={copy.close}
          onClick={closeMenu}
        />
      )}
      <div className="appBody">
        <header className="topbar">
          <button
            ref={menuButton}
            className="iconButton mobileMenu"
            aria-label={copy.menu}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen(!menuOpen)}
          >
            ☰
          </button>
          <span className="breadcrumb">{location}</span>
          <button
            className="searchButton"
            aria-label={copy.search}
            onClick={() => setSearchOpen(true)}
          >
            <span aria-hidden="true">⌕</span>
            <span>{copy.search}</span>
            <kbd>⌘ K</kbd>
          </button>
          <div className="topbarTools">
            <span
              className={`serviceState ${health.error ? "serviceOffline" : ""}`}
              title={
                health.data
                  ? `${health.data.environment} · ${health.data.broker_mode}`
                  : undefined
              }
            >
              <i aria-hidden="true" />
              {health.error
                ? copy.offline
                : health.data
                  ? copy.online
                  : copy.connecting}
            </span>
            <LanguageSelector />
            <label className="themeControl">
              <span className="srOnly">{copy.theme}</span>
              <select
                aria-label={copy.theme}
                value={preferences.theme}
                onChange={(event) =>
                  update({
                    theme: event.target.value as typeof preferences.theme,
                  })
                }
              >
                <option value="system">{copy.system}</option>
                <option value="light">{copy.light}</option>
                <option value="dark">{copy.dark}</option>
              </select>
            </label>
          </div>
        </header>
        <main
          id="main-content"
          tabIndex={-1}
          className="workspace"
          key={pathname}
        >
          {children}
        </main>
        <footer>{copy.footer}</footer>
      </div>
      {searchOpen && <CommandPalette onClose={() => setSearchOpen(false)} />}
    </div>
  );
}
