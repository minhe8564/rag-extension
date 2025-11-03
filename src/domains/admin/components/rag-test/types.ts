export type Collection = {
  id: string;
  name: string;
  ingestTemplate?: string;
};

export type QueryTemplate = {
  id: string;
  name: string;
  description?: string;
  body: string;
};

export type IngestStrategy = {
  id: string;
  name: string;
  notes?: string;
};

export type QueryStrategy = {
  id: string;
  name: string;
  body: string;
};
