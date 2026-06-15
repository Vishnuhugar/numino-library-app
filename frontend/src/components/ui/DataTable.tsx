"use client";
import React from 'react';

type Column<T> = {
  key: string;
  title: string;
  className?: string;
  render?: (row: T) => React.ReactNode;
};

export default function DataTable<T>({ columns, data, rowKey }: {
  columns: Column<T>[];
  data: T[];
  rowKey?: (row: T) => string;
}) {
  return (
    <table className="lib-table">
      <thead>
        <tr>
          {columns.map(c => <th key={c.key} className={c.className}>{c.title}</th>)}
        </tr>
      </thead>
      <tbody>
        {data.map((row, i) => (
          <tr key={rowKey ? rowKey(row) : (i + '')}>
            {columns.map(c => (
              <td key={c.key} className={c.className}>{c.render ? c.render(row) : (row as any)[c.key]}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
