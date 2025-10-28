import PageHeader from '@/domains/admin/components/documents/PageHeader';
import UploadFile from '@/domains/admin/components/documents/UploadFile';
import UploadList from '@/domains/admin/components/documents/UploadList';
import ColSection from '@/domains/admin/components/documents/ColSection';
import SelectVectorization from '@/domains/admin/components/documents/SelectVectorization';
import VecProcess from '@/domains/admin/components/documents/VecProcess';
import ColList from '@/domains/admin/components/documents/ColList';

export default function Documents() {
  return (
    <main>
      <PageHeader />
      <UploadFile />
      <div className='flex gap-4'>
      <UploadList />
      <ColSection />
      </div>
      <SelectVectorization />
      <VecProcess />
      <ColList />
    </main>
  );
}
