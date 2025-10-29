import PageHeader from '@/domains/admin/components/documents/PageHeader';
import UploadFile from '@/domains/admin/components/documents/UploadFile';
import UploadList from '@/domains/admin/components/documents/UploadList';
import ColSection from '@/domains/admin/components/documents/ColSection';
import SelectVectorization from '@/domains/admin/components/documents/SelectVectorization';

export default function UploadTab() {
  return (
    <>
      <UploadFile />
      <div className="flex gap-4">
        <UploadList />
        <ColSection />
      </div>
      <SelectVectorization />
    </>
  );
}
