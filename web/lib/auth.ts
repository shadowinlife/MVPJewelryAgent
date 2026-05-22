import { cookies } from "next/headers";

import usersData from "@/lib/mock/users.json";
import type { User } from "@/lib/types/domain";

const USER_COOKIE = "yq_user";
const ADMIN_COOKIE = "yq_admin";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 7;

const users = usersData.users as User[];
const adminCred = usersData.admin;

export function validatePhone(phone: string): boolean {
  return /^1[3-9]\d{9}$/.test(phone);
}

export function validateOtp(otp: string): boolean {
  return /^\d{6}$/.test(otp);
}

export function findUserByPhone(phone: string): User {
  const match = users.find((u) => u.phone === phone);
  return match ?? users[0];
}

export async function setUserSession(userId: string): Promise<void> {
  const jar = await cookies();
  jar.set(USER_COOKIE, userId, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: COOKIE_MAX_AGE,
  });
}

export async function clearUserSession(): Promise<void> {
  const jar = await cookies();
  jar.delete(USER_COOKIE);
}

export async function hasUserCookie(): Promise<boolean> {
  const jar = await cookies();
  return Boolean(jar.get(USER_COOKIE)?.value);
}

export async function getCurrentUser(): Promise<User | null> {
  const jar = await cookies();
  const id = jar.get(USER_COOKIE)?.value;
  if (id) {
    return users.find((u) => u.id === id) ?? null;
  }
  // Mock-mode auto-login: 内测期间未登录直接绑定 u_001 (pro tier),便于走查页面。
  // 真后端接入或关闭 NEXT_PUBLIC_MOCK_MODE 后该分支自动失效。
  if (process.env.NEXT_PUBLIC_MOCK_MODE === "true") {
    return users[0] ?? null;
  }
  return null;
}

export function verifyAdmin(username: string, password: string): boolean {
  return username === adminCred.username && password === adminCred.password;
}

export async function setAdminSession(): Promise<void> {
  const jar = await cookies();
  jar.set(ADMIN_COOKIE, "1", {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: COOKIE_MAX_AGE,
  });
}

export async function clearAdminSession(): Promise<void> {
  const jar = await cookies();
  jar.delete(ADMIN_COOKIE);
}

export async function isAdminAuthenticated(): Promise<boolean> {
  const jar = await cookies();
  return jar.get(ADMIN_COOKIE)?.value === "1";
}
