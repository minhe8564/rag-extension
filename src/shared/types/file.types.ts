export interface Category {
  categoryNo: string;
  name: string;
}

export interface GetCategoriesResult {
  data: Category[];
}
