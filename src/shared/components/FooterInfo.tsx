import gitlabLogo from '@/assets/logos/gitlab-logo.png';
import notionLogo from '@/assets/logos/notion-logo.png';
import ragExtensionLogo from '@/assets/logos/rag-extension-logo.png';

type Brand = 'retina' | 'hebees';

type LinkItem = {
  href: string;
  label: string;
  iconSrc?: string;
};

const brandColor: Record<Brand, string> = {
  retina: 'var(--color-retina)',
  hebees: 'var(--color-hebees)',
};

export default function FooterInfo({
  brand = 'hebees',
  links = [
    {
      href: 'https://www.notion.so/RAG-27fab603db8b80a8aaede0341b34645a?source=copy_link',
      label: 'Notion',
      iconSrc: notionLogo,
    },
    { href: 'https://lab.ssafy.com/s13-final/S13P31S407', label: 'GitLab', iconSrc: gitlabLogo },
  ],
}: {
  brand?: Brand;
  links?: LinkItem[];
}) {
  const accent = brandColor[brand];
  const year = new Date().getFullYear();

  const team: Array<{ name: string; role: string }> = [
    { name: '이재원', role: 'AI' },
    { name: '최민석', role: 'Infra' },
    { name: '이민희', role: 'Frontend' },
    { name: '이진모', role: 'Frontend' },
    { name: '배준수', role: 'Backend' },
    { name: '김태윤', role: 'Backend' },
    { name: '백종석', role: 'Backend' },
  ];

  return (
    <footer className="w-full px-4 py-16">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-[80px] w-[80px] items-center justify-center rounded-xl bg-white border border-gray-200 overflow-hidden">
            <img
              src={ragExtensionLogo}
              alt="RAG Extension 로고"
              className="h-full w-full object-contain"
              loading="lazy"
            />
          </div>

          <div className="space-y-1">
            <p className="text-sm font-semibold text-neutral-900">RAG Extension</p>
            <p className="text-xs text-neutral-500">
              SSAFY 13기 · S407
              <span className="mx-1 text-neutral-300">•</span>
              HEBEES
            </p>
            <p className="text-[11px] text-neutral-400">
              made by <span className="font-medium text-neutral-500">예리 코치님</span>
            </p>
          </div>
        </div>

        <nav>
          <ul className="flex flex-wrap items-center justify-start gap-4 md:justify-end">
            {links.map((l) => (
              <li key={l.href}>
                <a
                  href={l.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-full border border-neutral-200 bg-white px-3 py-1.5 text-sm font-medium text-neutral-700 hover:bg-neutral-50 hover:border-neutral-300 transition-colors"
                >
                  {l.iconSrc && <img src={l.iconSrc} alt="" className="h-4 w-4 opacity-80" />}
                  <span>{l.label}</span>
                  <span className="sr-only">(새 창)</span>
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>

      <div className="mt-4 h-px w-full" />

      <div className="mt-3 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <ul className="flex flex-wrap gap-x-7 gap-y-1 text-[12px] text-neutral-700">
          {team.map((m) => (
            <li key={m.name} className="flex items-center gap-1 leading-none">
              <span className="font-medium text-neutral-900">{m.name}</span>
              <span className="text-neutral-300">•</span>
              <span className="text-xs" style={{ color: accent }}>
                {m.role}
              </span>
            </li>
          ))}
        </ul>

        <p className="text-[11px] text-neutral-400">
          © {year}{' '}
          <span style={{ color: accent }} className="font-medium">
            Hebees
          </span>
          . All rights reserved.
        </p>
      </div>
    </footer>
  );
}
