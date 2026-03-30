import { Link, useLocation } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";
import { cn } from "@/lib/utils";

interface BreadcrumbsProps {
  className?: string;
  customLabels?: Record<string, string>;
}

export function Breadcrumbs({ className, customLabels = {} }: BreadcrumbsProps) {
  const location = useLocation();
  const pathnames = location.pathname.split("/").filter((x) => x);

  if (pathnames.length === 0) return null;

  return (
    <nav className={cn("flex items-center text-sm text-muted-foreground", className)}>
      <ol className="flex items-center space-x-2">
        <li>
          <Link to="/dashboard" className="hover:text-foreground transition-colors">
            <Home className="h-4 w-4" />
          </Link>
        </li>
        
        {pathnames.map((value, index) => {
          const last = index === pathnames.length - 1;
          const to = `/${pathnames.slice(0, index + 1).join("/")}`;
          
          // Use custom label or capitalize/format the path slug
          let label = customLabels[value] || (value?.charAt(0) || '?').toUpperCase() + (value?.slice(1) || '').replace(/-/g, " ");
          
          // Handle UUIDs or IDs (very rough check)
          if (value.length > 20 || (value.includes("-") && value.split("-").length > 2)) {
            label = "Details";
          }

          return (
            <li key={to} className="flex items-center space-x-2">
              <ChevronRight className="h-4 w-4 shrink-0" />
              {last ? (
                <span className="font-medium text-foreground truncate max-w-[150px]">
                  {label}
                </span>
              ) : (
                <Link to={to} className="hover:text-foreground transition-colors truncate max-w-[150px]">
                  {label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
