export default function Loading() {
  return <div className="loading-grid" aria-label="جارٍ التحميل">{Array.from({ length: 6 }, (_, index) => <div className="skeleton" key={index} />)}</div>;
}

