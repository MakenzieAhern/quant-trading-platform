import type { AnchorHTMLAttributes, MouseEvent } from "react";

import { navigate, navigateBack } from "../utils/navigation";

export function Link({
  href = "/",
  onClick,
  back = false,
  ...props
}: AnchorHTMLAttributes<HTMLAnchorElement> & { back?: boolean }) {
  const follow = (event: MouseEvent<HTMLAnchorElement>) => {
    onClick?.(event);
    if (
      !event.defaultPrevented &&
      event.button === 0 &&
      !event.metaKey &&
      !event.ctrlKey &&
      !event.shiftKey &&
      !event.altKey
    ) {
      event.preventDefault();
      if (back) navigateBack(href);
      else navigate(href);
    }
  };
  return <a {...props} href={href} onClick={follow} />;
}
