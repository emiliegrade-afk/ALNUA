import type { PostPlatform, PostStatus } from "@/components/content/content.constants";

import { hubFetch } from "./hub-fetch";

export interface Post {
  id: string;
  project_id: string;
  platform: PostPlatform;
  content_type: string;
  text_content: string;
  image_prompt: string | null;
  video_script: string | null;
  hashtags: string[];
  scheduled_at: string;
  published_at: string | null;
  status: PostStatus;
  created_at: string;
}

export interface GeneratePostsResponse {
  posts_created: number;
  posts: Post[];
}

export async function generatePosts(body: {
  project_id: string;
  dev_log: string;
  content_types: string[];
  platforms: string[];
  alnua_global?: boolean;
}): Promise<GeneratePostsResponse> {
  return hubFetch<GeneratePostsResponse>("/agents/content/generate", {
    method: "POST",
    body: JSON.stringify(body),
    timeoutMs: 120_000,
  });
}

export async function fetchPosts(params?: {
  status?: string;
  project_id?: string;
  platform?: string;
}): Promise<Post[]> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.project_id) qs.set("project_id", params.project_id);
  if (params?.platform) qs.set("platform", params.platform);
  const query = qs.toString();
  return hubFetch<Post[]>(`/posts${query ? `?${query}` : ""}`);
}

export async function updatePost(
  postId: string,
  body: {
    status?: PostStatus;
    text_content?: string;
    hashtags?: string[];
    scheduled_at?: string;
  }
): Promise<Post> {
  return hubFetch<Post>(`/posts/${postId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export function computePostStats(posts: Post[]) {
  const now = new Date();
  const weekAgo = new Date(now);
  weekAgo.setDate(weekAgo.getDate() - 7);
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);

  return {
    pending: posts.filter((p) => p.status === "pending_approval").length,
    approvedThisWeek: posts.filter(
      (p) =>
        p.status === "approved" &&
        new Date(p.created_at) >= weekAgo
    ).length,
    publishedThisMonth: posts.filter(
      (p) =>
        p.status === "published" &&
        new Date(p.published_at ?? p.created_at) >= monthStart
    ).length,
  };
}
