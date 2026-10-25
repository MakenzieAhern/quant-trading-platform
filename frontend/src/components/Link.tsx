import type { AnchorHTMLAttributes, MouseEvent } from "react";

import { managedReturnHref, navigate, navigateBack } from "../utils/navigation";

export function Link({
  href = "/",
  onClick,
  back = false,
  ...props
}: AnchorHTMLAttributes<HTMLAnchorElement> & { back?: boolean }) {
  const destination = back ? managedReturnHref(href) : href;
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
      if (back) navigateBack(destination);
      else navigate(destination);
    }
  };
  return <a {...props} href={destination} onClick={follow} />;
}
