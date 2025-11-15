import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';

type Props = {
  children: string;
  className?: string;
};

export default function ChatMarkdown({ children, className = '' }: Props) {
  let normalized = children.replace(/\\n/g, '\n');
  normalized = normalized.replace(/\*\*([\s\S]+?)\*\*/g, '\uE000$1\uE001');
  normalized = normalized.replace(/\*\*\s*"/g, '\\*\\*"').replace(/"\s*\*\*/g, '"\\*\\*');
  normalized = normalized.replace(/\uE000/g, '**').replace(/\uE001/g, '**');

  return (
    <div
      className={[
        'prose prose-sm max-w-none leading-[1.8]',
        '[&>hr]:my-6 [&>hr]:border-t [&>hr]:border-gray-200',

        'overflow-x-auto',
        '[-webkit-overflow-scrolling:touch]',

        '[&_table]:w-[75%]',
        '[&_table]:min-w-[520px]',
        '[&_table]:border-separate',
        '[&_table]:border-spacing-0',
        '[&_table]:bg-white',

        // thead
        '[&_thead_th]:text-left',
        '[&_thead_th]:whitespace-nowrap',
        '[&_thead_th]:text-gray-700',
        '[&_thead_th]:font-bold',
        '[&_thead_th]:text-sm',
        '[&_thead_th]:uppercase',
        '[&_thead_th]:tracking-wide',
        '[&_thead_th]:px-4',
        '[&_thead_th]:py-2.5',
        '[&_thead_th]:border-b',
        '[&_thead_th]:border-gray-200',

        // tbody
        '[&_tbody_td]:text-left',
        '[&_tbody_td]:px-4',
        '[&_tbody_td]:py-2.5',
        '[&_tbody_td]:text-sm',
        '[&_tbody_td]:align-middle',
        '[&_tbody_td]:text-gray-800',
        '[&_tbody_td]:border-b',
        '[&_tbody_td]:border-gray-100',

        '[&_tbody_td:first-child]:pl-5',
        '[&_tbody_td:last-child]:pr-5',

        '[&_table_*]:break-words',
        '[&_table_*]:whitespace-pre-wrap',

        className,
      ].join(' ')}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>{normalized}</ReactMarkdown>
    </div>
  );
}
