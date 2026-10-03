export function exportToCSV(filename: string, headers: string[], rows: string[][]) {
  // Add BOM for Turkish characters in Excel
  const BOM = '\uFEFF';
  const csv = BOM + [
    headers.join(';'),
    ...rows.map(row => row.map(cell => `"${(cell ?? '').toString().replace(/"/g, '""')}"`).join(';'))
  ].join('\n');
  
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}_${new Date().toISOString().slice(0,10)}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}
