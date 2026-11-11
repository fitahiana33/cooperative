import { api } from "../api";
import type {
  PasswordChange,
  ProfileUpdate,
  User,
  UserCreate,
  UserUpdate,
} from "../../models/user/model";

export const userService = {
  async photo(id?: number): Promise<Blob> {
    return (
      await api.get(
        id === undefined ? "/users/me/photo" : `/users/${id}/photo`,
        { responseType: "blob" },
      )
    ).data;
  },
  async uploadPhoto(file: File): Promise<User> {
    const data = new FormData();
    data.append("file", file);
    return (
      await api.put<User>("/users/me/photo", data, {
        headers: { "Content-Type": undefined },
      })
    ).data;
  },
  async removePhoto(): Promise<User> {
    return (await api.delete<User>("/users/me/photo")).data;
  },
  async me(): Promise<User> {
    return (await api.get<User>("/users/me")).data;
  },
  async updateMe(payload: ProfileUpdate): Promise<User> {
    return (await api.put<User>("/users/me", payload)).data;
  },
  async changePassword(payload: PasswordChange): Promise<void> {
    await api.post("/users/me/password", payload);
  },
  async list(
    params: {
      page?: number;
      page_size?: number;
      search?: string;
      role?: string;
      is_active?: boolean;
      created_from?: string;
      created_to?: string;
      sort_by?: string;
      sort_order?: string;
    } = {},
  ) {
    return (
      await api.get<{
        items: User[];
        total: number;
        page: number;
        page_size: number;
        pages: number;
      }>("/users", { params })
    ).data;
  },
  async get(id: number): Promise<User> {
    return (await api.get<User>(`/users/${id}`)).data;
  },
  async create(payload: UserCreate): Promise<User> {
    return (await api.post<User>("/users", payload)).data;
  },
  async update(id: number, payload: UserUpdate): Promise<User> {
    return (await api.put<User>(`/users/${id}`, payload)).data;
  },
  async toggle(id: number): Promise<User> {
    return (await api.patch<User>(`/users/${id}/toggle`)).data;
  },
  async delete(id: number): Promise<void> {
    await api.delete(`/users/${id}`);
  },
  async assignRole(userId: number, roleId: number): Promise<User> {
    return (await api.post<User>(`/users/${userId}/roles/${roleId}`)).data;
  },
  async revokeRole(userId: number, roleId: number): Promise<User> {
    return (await api.delete<User>(`/users/${userId}/roles/${roleId}`)).data;
  },
};
