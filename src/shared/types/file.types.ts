export type OnNameConflict = 'reject' | 'overwrite';

export type RagStatus = 'PENDING' | 'INGESTING' | 'COMPLETED' | 'FAILED';

export type UploadedDoc = {
  id: string;
  name: string;
  sizeKB: number;
  createdAt?: string;
  category?: string;
  categoryId?: string;
  type: string;
  file?: File;
  fileNo?: string;
  status?: RagStatus | string;
};

export interface UploadFilesParams {
  files: File[];
  categoryNo: string;
  bucket?: string;
  onNameConflict?: OnNameConflict;
}

export interface UploadFilesResult {
  data: { fileNos: string[] };
}

export interface Category {
  categoryNo: string;
  name: string;
}

export interface GetCategoriesResult {
  data: Category[];
}

export interface RawMyDoc {
  fileNo: string;
  name: string;
  size: number;
  type: string;
  bucket: string;
  path: string;
  status: 'PENDING' | 'INGESTING' | 'COMPLETED' | 'FAILED';
  categoryNo: string;
  collectionNo: string;
  createdAt: string;
  originalFile?: File;
}

export interface MyDoc {
  fileNo: string;
  name: string;
  sizeKB: number;
  type: RawMyDoc['type'];
  bucket: string;
  path: string;
  status: 'PENDING' | 'INGESTING' | 'COMPLETED' | 'FAILED';
  categoryNo: string;
  collectionNo: string;
  createdAt: string;
}

export interface ServerPagination {
  pageNum: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  hasNext: boolean;
}

export interface FilesResponse<T> {
  status: number;
  code: string;
  message: string;
  isSuccess: boolean;
  result: {
    data: T[];
    pagination: ServerPagination;
  };
}

export interface FetchMyDocsNormalized {
  items: MyDoc[];
  total: number;
  totalPages: number;
  hasNext: boolean;
  pageNum: number;
  pageSize: number;
}

export type PresignedUrl = { url: string };

export type DeleteFileData = {
  fileNo: string;
  name: string;
  deleted: boolean;
};
