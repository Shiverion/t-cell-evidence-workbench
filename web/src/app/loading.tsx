export default function Loading() {
  return (
    <div aria-label="Loading analysis workspace" className="space-y-8">
      <div className="space-y-3 border-b border-line pb-8">
        <div className="skeleton h-3 w-44 rounded-full" />
        <div className="skeleton h-10 w-full max-w-3xl rounded-lg" />
        <div className="skeleton h-4 w-full max-w-2xl rounded-full" />
      </div>
      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="skeleton h-[28rem] rounded-xl" />
        <div className="space-y-3">
          <div className="skeleton h-28 rounded-xl" />
          <div className="skeleton h-28 rounded-xl" />
          <div className="skeleton h-28 rounded-xl" />
        </div>
      </div>
    </div>
  );
}
