/**
 * Homepage demo video.
 * Replace `DEMO_VIDEO` with one of the shapes below. Leave it null until a file or link exists.
 *
 * MP4:    { source: 'mp4', src: '/demo/nexus-demo.mp4' }
 * YouTube:{ source: 'youtube', url: 'https://www.youtube.com/watch?v=VIDEO_ID' }
 * Vimeo:  { source: 'vimeo', url: 'https://vimeo.com/123456789' }
 */
export type DemoVideo =
  | { source: 'mp4'; src: string; poster?: string }
  | { source: 'youtube'; url: string }
  | { source: 'vimeo'; url: string };

export const DEMO_VIDEO: DemoVideo | null = null;

export function youtubeId(url: string): string | null {
  try {
    const parsed = new URL(url);
    if (parsed.hostname === 'youtu.be') return parsed.pathname.slice(1) || null;
    if (parsed.hostname.includes('youtube.com')) {
      return parsed.searchParams.get('v') || parsed.pathname.split('/').filter(Boolean).pop() || null;
    }
  } catch {
    return null;
  }
  return null;
}

export function vimeoId(url: string): string | null {
  const match = url.match(/vimeo\.com\/(?:video\/)?(\d+)/);
  return match?.[1] ?? null;
}
