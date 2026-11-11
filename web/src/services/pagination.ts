export interface Page<T> {
  items: T[];
  page: number;
  pages: number;
  page_size: number;
  total: number;
}

/** Complete reference lists; never silently discard the second page. */
export async function allPages<T>(
  fetchPage: (params: Record<string, unknown>) => Promise<Page<T>>,
  params: Record<string, unknown> = {},
): Promise<Page<T>> {
  const first = await fetchPage({ ...params, page: 1, page_size: 100 });
  const items = [...first.items];
  for (let page = 2; page <= first.pages; page++) {
    const next = await fetchPage({ ...params, page, page_size: 100 });
    items.push(...next.items);
  }
  return { ...first, items };
}
