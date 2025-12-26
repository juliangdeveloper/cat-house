import apiClient from '../client';

export interface Installation {
  id: string;
  catId: string;
  userId: string;
  status: 'active' | 'inactive' | 'installing' | 'failed';
  config: Record<string, any>;
  installed_at: string;
  updated_at: string;
}

export interface InstallCatRequest {
  catId: string;
  config?: Record<string, any>;
}

export const installationService = {
  getInstallations: async (): Promise<Installation[]> => {
    const response = await apiClient.get<{ installations: Installation[] }>(
      '/api/v1/installations'
    );
    return response.data.installations;
  },

  getInstallationById: async (id: string): Promise<Installation> => {
    const response = await apiClient.get<Installation>(`/api/v1/installations/${id}`);
    return response.data;
  },

  installCat: async (data: InstallCatRequest): Promise<Installation> => {
    const response = await apiClient.post<Installation>(
      `/api/v1/install/${data.catId}`,
      { config: data.config }
    );
    return response.data;
  },

  uninstallCat: async (installationId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/installations/${installationId}`);
  },

  updateInstallation: async (
    installationId: string,
    config: Record<string, any>
  ): Promise<Installation> => {
    const response = await apiClient.patch<Installation>(
      `/api/v1/installations/${installationId}`,
      { config }
    );
    return response.data;
  },
};
