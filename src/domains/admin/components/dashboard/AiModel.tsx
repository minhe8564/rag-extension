import ModelToken from '@/domains/admin/components/dashboard/ModelToken';
import ModelResponse from '@/domains/admin/components/dashboard/ModelResponse';

export default function AIModel() {
  return (
    <section className="flex flex-row gap-4 my-3">
      <div className="w-1/2">
        <ModelToken />
      </div>
      <div className="w-1/2">
        <ModelResponse />
      </div>
    </section>
  );
}
