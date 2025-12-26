import apiClient from '../client';

export interface Cat {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  icon_url?: string;
  category: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface CatalogResponse {
  cats: Cat[];
  total: number;
  page: number;
  pageSize: number;
}

export const catalogService = {
  getCats: async (params?: {
    page?: number;
    pageSize?: number;
    category?: string;
    search?: string;
  }): Promise<CatalogResponse> => {
    const response = await apiClient.get<CatalogResponse>('/api/v1/catalog/cats', {
      params,
    });
    return response.data;
  },

  getCatById: async (id: string): Promise<Cat> => {
    const response = await apiClient.get<Cat>(`/api/v1/catalog/cats/${id}`);
    return response.data;
  },

  searchCats: async (query: string): Promise<Cat[]> => {
    const response = await apiClient.get<{ cats: Cat[] }>('/api/v1/catalog/cats/search', {
      params: { q: query },
    });
    return response.data.cats;
  },
};
