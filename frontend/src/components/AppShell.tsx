import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type MouseEvent,
  type ReactNode,
} from "react";
import { getHealth } from "../api/health";
import { useApiResource } from "../hooks/useApiResource";
import { usePathname } from "../utils/navigation";
import { useProductCopy } from "../product/copy";
import { usePreferences } from "../product/preferences";
import { CommandPalette } from "../product/CommandPalette";
import { experimentApi } from "../product/experiments/api";
import { useCurrentPageData } from "../product/dataContext";
import { formatUtc } from "../utils/format";
import { Link } from "./Link";
import { LanguageSelector } from "./LanguageSelector";

export function AppShell({ children }: { children: ReactNode }) {
  const copy = useProductCopy();
  const pathname = usePathname();
  const previousPathname = useRef(pathname);
  const { preferences, update, unsaved } = usePreferences();
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const sidebar = useRef<HTMLElement>(null);
  const menuButton = useRef<HTMLButtonElement>(null);
  const lastFocused = useRef<Element | null>(null);
  const resizeFocus = useRef<Element | null>(null);
  const [refresh, setRefresh] = useState(0);
  const lastCheck = useRef(0);
  const pageData = useCurrentPageData();
  const closeMenu = () => {
    setMenuOpen(false);
    requestAnimationFrame(() => menuButton.current?.focus());
  };
  const closeCurrentSidebarLink = (event: MouseEvent<HTMLAnchorElement>) => {
    if (
      menuOpen &&
      event.button === 0 &&
      !event.metaKey &&
      !event.ctrlKey &&
      !event.shiftKey &&
      !event.altKey &&
      !event.defaultPrevented &&
      event.currentTarget.href === window.location.href
    )
      closeMenu();
  };
  const health = useApiResource(
    async (signal) => {
      lastCheck.current = Date.now();
      const result = await getHealth(signal);
      return { ...result, checkedAt: new Date().toISOString() };
    },
    [refresh],
  );
  const data = useApiResource(
    (signal) => experimentApi.capabilities(signal),
    [refresh],
  );
  const refreshing = health.loading || data.loading;
  const available =
    data.data?.datasets.find(
      (item) => item.mode === "historical_exploration" && item.available,
    ) ?? data.data?.datasets.find((item) => item.available);
  const displayedData =
    pageData ??
    (available ? { mode: available.mode, asOf: available.as_of } : null);
  const serviceStatus = health.error
    ? copy.offline
    : health.data
      ? copy.online
      : copy.connecting;
  const links = [
    { href: "/", label: copy.home, icon: "◫" },
    { href: "/markets", label: copy.markets, icon: "▥" },
    { href: "/strategies", label: copy.strategies, icon: "◇" },
    { href: "/experiments", label: copy.research, icon: "▤" },
    { href: "/tasks", label: copy.tasks, icon: "◷" },
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
  useLayoutEffect(() => {
    const focused = resizeFocus.current;
    if (menuOpen || !focused) return;
    resizeFocus.current = null;
    if (
      document.activeElement === focused ||
      document.activeElement === document.body
    )
      document.getElementById("main-content")?.focus({ preventScroll: true });
  }, [menuOpen]);
  useEffect(() => {
    const mobile = window.matchMedia?.("(max-width: 800px)");
    const leaveMobile = () => {
      const focused = document.activeElement;
      if (mobile?.matches) {
        if (
          sidebar.current?.contains(focused) ||
          (focused === document.body &&
            sidebar.current?.contains(lastFocused.current))
        )
          menuButton.current?.focus({ preventScroll: true });
        return;
      }
      const mobileControl = focused?.matches(".mobileMenu, .sidebarBackdrop")
        ? focused
        : focused === document.body &&
            lastFocused.current?.matches(".mobileMenu, .sidebarBackdrop")
          ? lastFocused.current
          : null;
      const menuWasOpen = sidebar.current?.classList.contains("sidebarOpen");
      if (mobileControl && menuWasOpen) resizeFocus.current = mobileControl;
      setMenuOpen(false);
      if (mobileControl && !menuWasOpen)
        document.getElementById("main-content")?.focus({ preventScroll: true });
    };
    mobile?.addEventListener("change", leaveMobile);
    return () => mobile?.removeEventListener("change", leaveMobile);
  }, []);
  useEffect(() => {
    const refreshOnReturn = () => {
      if (
        document.visibilityState !== "hidden" &&
        Date.now() - lastCheck.current >= 10_000
      ) {
        lastCheck.current = Date.now();
        setRefresh((value) => value + 1);
      }
    };
    window.addEventListener("focus", refreshOnReturn);
    document.addEventListener("visibilitychange", refreshOnReturn);
    const timer = window.setInterval(refreshOnReturn, 30_000);
    return () => {
      window.removeEventListener("focus", refreshOnReturn);
      document.removeEventListener("visibilitychange", refreshOnReturn);
      window.clearInterval(timer);
    };
  }, []);
  useEffect(() => {
    if (previousPathname.current === pathname) return;
    previousPathname.current = pathname;
    document.getElementById("main-content")?.focus({ preventScroll: true });
  }, [pathname]);
  useEffect(() => {
    document.documentElement.dataset.theme = preferences.theme;
    document.documentElement.dataset.motion = preferences.motion;
    document.documentElement.dataset.marketColors = preferences.marketColors;
  }, [preferences]);
  useEffect(() => {
    const handle = (event: KeyboardEvent) => {
      if (sidebar.current?.classList.contains("sidebarOpen")) {
        if (event.key === "Escape") {
          event.preventDefault();
          closeMenu();
        }
        if (event.key === "Tab") {
          const items = sidebar.current.querySelectorAll<HTMLElement>(
            "a[href], button:not([disabled])",
          );
          const first = items[0];
          const last = items[items.length - 1];
          if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last?.focus();
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first?.focus();
          }
        }
        return;
      }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearchOpen((open) => !open);
      }
    };
    const closeAfterNavigation = (event: PopStateEvent) => {
      if (
        window.location.pathname !== pathname ||
        event.state?.quantNavigationApproved
      )
        setMenuOpen(false);
    };
    window.addEventListener("keydown", handle);
    window.addEventListener("popstate", closeAfterNavigation);
    return () => {
      window.removeEventListener("keydown", handle);
      window.removeEventListener("popstate", closeAfterNavigation);
    };
  }, [pathname]);
  return (
    <div
      className="appShell"
      onFocusCapture={(event) => {
        lastFocused.current = event.target;
      }}
    >
      <a className="skipLink" href="#main-content" inert={menuOpen}>
        {copy.skipContent}
      </a>
      <aside
        ref={sidebar}
        className={`sidebar ${menuOpen ? "sidebarOpen" : ""}`}
        role={menuOpen ? "dialog" : undefined}
        aria-modal={menuOpen ? true : undefined}
        aria-label={menuOpen ? copy.navigation : undefined}
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
          onClick={closeCurrentSidebarLink}
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
        <nav aria-label={copy.navigation}>
          {links.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={closeCurrentSidebarLink}
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
          <nav aria-label={copy.help}>
            <Link
              href="/help"
              onClick={closeCurrentSidebarLink}
              aria-current={pathname === "/help" ? "page" : undefined}
            >
              <span className="navIcon" aria-hidden="true">
                ?
              </span>
              {copy.help}
            </Link>
            <Link
              href="/settings"
              onClick={closeCurrentSidebarLink}
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
          tabIndex={-1}
        />
      )}
      <div className="appBody" inert={menuOpen}>
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
            <kbd>Ctrl / ⌘ K</kbd>
          </button>
          <Link className="topbarData" href="/data" title={copy.dateZone}>
            <span>
              {pageData
                ? pageData.dateKind === "snapshot"
                  ? copy.snapshotData
                  : pageData.dateKind === "observed"
                    ? copy.pageData
                    : copy.requestedData
                : copy.catalogue}
            </span>
            <strong>
              {displayedData
                ? `${displayedData.mode === "synthetic_demo" ? copy.demo : copy.historical} · ${displayedData.asOf ?? copy.notRecorded}`
                : data.loading
                  ? copy.loading
                  : copy.unavailable}
            </strong>
          </Link>
          <div className="topbarTools">
            <button
              type="button"
              className={`serviceState ${health.error ? "serviceOffline" : ""}`}
              aria-label={copy.refreshStatus}
              aria-describedby="service-health-status"
              aria-disabled={refreshing}
              onClick={() => {
                if (!refreshing) setRefresh((value) => value + 1);
              }}
            >
              <i aria-hidden="true" />
              <span className="serviceText">{serviceStatus}</span>
              {health.data && (
                <span className="srOnly">
                  {copy.checkedAt}: {formatUtc(health.data.checkedAt)}
                </span>
              )}
            </button>
            <span id="service-health-status" className="srOnly" role="status">
              {serviceStatus}
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
        {unsaved && pathname !== "/settings" && (
          <p className="preferenceWarning" role="status">
            {copy.unsaved}
          </p>
        )}
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
