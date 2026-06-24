type HighlightedTextProps = {
  text: string;
  query: string;
};

export default function HighlightedText({
  text,
  query,
}: HighlightedTextProps) {
  const normalizedText = text ?? "";
  const normalizedQuery = query.trim();

  if (!normalizedQuery) {
    return <>{normalizedText}</>;
  }

  const lowerText = normalizedText.toLocaleLowerCase();
  const lowerQuery = normalizedQuery.toLocaleLowerCase();
  const matchIndex = lowerText.indexOf(lowerQuery);

  if (matchIndex === -1) {
    return <>{normalizedText}</>;
  }

  const matchEnd = matchIndex + normalizedQuery.length;

  return (
    <>
      {normalizedText.slice(0, matchIndex)}
      <mark className="rounded bg-[#3b82f6] px-0.5 text-white">
        {normalizedText.slice(matchIndex, matchEnd)}
      </mark>
      {normalizedText.slice(matchEnd)}
    </>
  );
}
