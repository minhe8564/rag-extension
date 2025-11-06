import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type Props = {
  children: string;
  className?: string;
};

export default function ChatMarkdown({ children, className = '' }: Props) {
  return (
    <div
      className={`
        prose prose-sm max-w-none leading-[1.8]
        [&>hr]:my-6 [&>hr]:border-t [&>hr]:border-gray-200
        ${className}
      `}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  );
}
