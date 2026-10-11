const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export type RecommendationMode = "github" | "text";

export interface RecommendPayload {
    mode: RecommendationMode;
    query: string;
    language?: string;
}

export interface IssueRecommendation {
    number: number;
    title: string;
    url: string;
    tags: string[];
    why: string[];
}

export interface Recommendation {
    repo_id: string;
    name: string;
    owner: string;
    description: string;
    language: string;
    stars: number;
    url: string;
    probability: number;
    why: string[];
    issues: IssueRecommendation[];
}

export interface RecommendResponse {
    status: string;
    query: string;
    mode: RecommendationMode;
    user: Record<string, unknown>;
    repos: Recommendation[];
}

export async function fetchRecommendations(payload: RecommendPayload): Promise<RecommendResponse> {
    const response = await fetch(`${API_BASE_URL}/api/recommend`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
            errorData?.detail || `Recommendation request failed with status: ${response.status}`
        );
    }

    return response.json();
}
