import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import { cn } from "../../lib/cn";

const remarkPlugins = [remarkGfm, remarkBreaks];

function heading(Tag, className) {
  function Heading({ children }) {
    return <Tag className={className}>{children}</Tag>;
  }
  Heading.displayName = `Md${Tag}`;
  return Heading;
}

const components = {
  p: ({ children }) => (
    <p className="mb-2 last:mb-0 text-[0.95rem] leading-snug text-tinta">{children}</p>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-tinta">{children}</strong>
  ),
  em: ({ children }) => <em className="italic">{children}</em>,
  ul: ({ children }) => (
    <ul className="mb-2 last:mb-0 list-disc space-y-1 pl-4 text-[0.95rem] leading-snug text-tinta">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="mb-2 last:mb-0 list-decimal space-y-1 pl-4 text-[0.95rem] leading-snug text-tinta">
      {children}
    </ol>
  ),
  li: ({ children }) => <li className="leading-snug">{children}</li>,
  h1: heading("h1", "mb-1.5 mt-2 first:mt-0 font-display text-[1.05rem] font-bold leading-snug text-tinta"),
  h2: heading("h2", "mb-1.5 mt-2 first:mt-0 font-display text-[1rem] font-bold leading-snug text-tinta"),
  h3: heading("h3", "mb-1 mt-2 first:mt-0 font-display text-[0.95rem] font-bold leading-snug text-tinta"),
  h4: heading("h4", "mb-1 mt-2 first:mt-0 text-[0.9rem] font-semibold leading-snug text-tinta"),
  blockquote: ({ children }) => (
    <blockquote className="mb-2 last:mb-0 border-l-2 border-violeta/40 pl-3 text-tinta-suave">
      {children}
    </blockquote>
  ),
  a: ({ href, children }) => (
    <a href={href} className="font-semibold text-violeta underline-offset-2 hover:underline" target="_blank" rel="noreferrer">
      {children}
    </a>
  ),
  hr: () => <hr className="my-2.5 border-linea" />,
  code: ({ className, children }) => {
    const block = /language-/.test(className || "");
    if (block) {
      return <code className={cn("font-mono text-[0.8rem]", className)}>{children}</code>;
    }
    return (
      <code className="rounded bg-papel-hondo px-1 py-0.5 font-mono text-[0.82em] text-tinta">
        {children}
      </code>
    );
  },
  pre: ({ children }) => (
    <pre className="mb-2 last:mb-0 overflow-x-auto rounded-xl bg-papel-hondo px-3 py-2 font-mono text-[0.8rem] leading-relaxed text-tinta">
      {children}
    </pre>
  ),
  table: ({ children }) => (
    <div className="mb-2 last:mb-0 overflow-x-auto">
      <table className="w-full border-collapse text-left text-[0.86rem]">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="border-b border-linea text-tinta-suave">{children}</thead>,
  th: ({ children }) => (
    <th className="px-2 py-1 font-semibold tabular-nums">{children}</th>
  ),
  td: ({ children }) => (
    <td className="px-2 py-1 tabular-nums text-tinta">{children}</td>
  ),
};

export function AngelaMarkdown({ text }) {
  if (!text) return null;
  return (
    <div className="angela-md min-w-0 text-[0.95rem] leading-snug text-tinta">
      <Markdown remarkPlugins={remarkPlugins} components={components}>
        {text}
      </Markdown>
    </div>
  );
}
