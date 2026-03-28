"use client";

import type { ReactNode } from "react";

import type { ScholarshipDetail } from "@/lib/types";

type ScholarshipCompareTableProps = {
  items: ScholarshipDetail[];
};

type CompareRow = {
  label: string;
  render: (item: ScholarshipDetail) => ReactNode;
};

function formatFunding(item: ScholarshipDetail) {
  const typeLabel = item.funding_type
    ? item.funding_type.replaceAll("_", " ")
    : "Not published";
  const hasRange =
    item.funding_amount_min !== null || item.funding_amount_max !== null;
  if (!hasRange) return `${typeLabel}`;

  const min = item.funding_amount_min ?? item.funding_amount_max;
  const max = item.funding_amount_max ?? item.funding_amount_min;
  return `${typeLabel} · $${min} – $${max}`;
}

const rows: CompareRow[] = [
  {
    label: "Title",
    render: (item) => item.title,
  },
  {
    label: "Provider",
    render: (item) => item.provider_name ?? "Not listed",
  },
  {
    label: "Country",
    render: (item) => item.country_code,
  },
  {
    label: "Degree",
    render: (item) => item.degree_levels.join(", ") || "Not listed",
  },
  {
    label: "Deadline",
    render: (item) =>
      item.deadline_at ? new Date(item.deadline_at).toLocaleDateString() : "Not listed",
  },
  {
    label: "Funding",
    render: (item) => formatFunding(item),
  },
  {
    label: "Requirements",
    render: (item) =>
      item.requirement_summary.length > 0
        ? item.requirement_summary.join("; ")
        : "Not published",
  },
  {
    label: "Source",
    render: (item) => (
      <a
        className="nav-link"
        href={item.source_url}
        rel="noreferrer"
        target="_blank"
        aria-label={`Open source for ${item.title} (new tab)`}
      >
        View source
      </a>
    ),
  },
];

export function ScholarshipCompareTable({ items }: ScholarshipCompareTableProps) {
  return (
    <div className="compare-table-wrap">
      <table className="compare-table">
        <thead>
          <tr>
            <th scope="col">Field</th>
            {items.map((item) => (
              <th key={item.scholarship_id} scope="col">
                {item.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label}>
              <th scope="row">{row.label}</th>
              {items.map((item) => (
                <td key={`${item.scholarship_id}-${row.label}`}>{row.render(item)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
