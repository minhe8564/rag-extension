import gitlabLogo from '@/assets/logos/gitlab-logo.png';
import notionLogo from '@/assets/logos/notion-logo.png';

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
    <footer className="w-full bg-white">
      <div className="relative mx-auto max-w-[960px] px-5 py-8">
        <div className="mb-5 text-center flex items-center justify-center gap-2">
          <span className="inline-flex items-center rounded-full border border-neutral-200 bg-white px-3 py-1 text-[11px] font-medium text-neutral-500">
            SSAFY 13기 · S407 RAG Extension
          </span>
          <span className="inline-flex items-center rounded-full border border-neutral-200 bg-white px-3 py-1 text-[11px] font-medium text-neutral-500">
            HEBEES
          </span>
        </div>

        <nav className="mb-4">
          <ul className="flex flex-wrap items-center justify-center gap-3">
            {links.map((l) => (
              <li key={l.href}>
                <a
                  href={l.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-[13px] font-medium text-neutral-700 hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-neutral-300 rounded-sm px-1"
                >
                  {l.iconSrc && <img src={l.iconSrc} alt="" className="h-4 w-4 opacity-80" />}
                  <span>{l.label}</span>
                  <span className="sr-only">(새 창)</span>
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="mx-auto my-8 w-full">
          <ul className="flex flex-wrap justify-center gap-x-6 gap-y-2 text-[13px] text-neutral-700">
            {team.map((m) => (
              <li key={m.name} className="flex items-center gap-2 leading-none">
                <span className="font-medium text-neutral-900">{m.name}</span>
                <span className="inline-block h-[3px] w-[3px] rounded-full bg-neutral-300"></span>
                <span className="text-[11px] text-neutral-500">{m.role}</span>
              </li>
            ))}
          </ul>
        </div>

        <p className="text-center text-xs text-neutral-400">
          © {year} <span style={{ color: accent }}>Hebees</span>. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
