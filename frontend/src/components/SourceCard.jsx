export default function SourceCard({ source }) {
	const title = source.title || source.document;
	const pageLabel = source.page ? `Page ${source.page}` : "";
	const details = [source.section, pageLabel].filter(Boolean).join(" · ");

	return (
		<li className="source-card">
			<span className="source-indicator" aria-hidden="true" />
			<span className="source-copy">
				<span className="source-title">{title}</span>
				{details && <span className="source-details">{details}</span>}
				{source.document && source.title && source.document !== source.title && (
					<span className="source-document">{source.document}</span>
				)}
			</span>
		</li>
	);
}
