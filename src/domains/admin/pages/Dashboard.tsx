import PageHeader from '@/domains/admin/components/dashboard/PageHeader';
import NumberBoard from '@/domains/admin/components/dashboard/NumberBoard';
import ChatbotUsage from '@/domains/admin/components/dashboard/ChatbotUsage';
import MonthlyUsage from '@/domains/admin/components/dashboard/MonthlyUsage';
import ChatbotFlow from '@/domains/admin/components/dashboard/ChatbotRealtime';
import ErrorTypes from '@/domains/admin/components/dashboard/ErrorTypes';
import ChatRoom from '@/domains/admin/components/dashboard/ChatRoom';
import ModelToken from '@/domains/admin/components/dashboard/ModelToken';
import ModelResponse from '@/domains/admin/components/dashboard/ModelResponse';
import KeywordMap from '@/domains/admin/components/dashboard/KeywordMap';

export default function Dashboard() {
  return (
    <section className="flex flex-col items-center">
      <PageHeader />

      <section className="w-full flex justify-center">
        <div className="origin-center w-full max-w-[95%] xl:max-w-[100%] px-6 space-y-2">
          <section className="grid grid-cols-12 gap-2 items-stretch">
            <div className="col-span-6 h-full">
              <NumberBoard />
            </div>
            <div className="col-span-6 h-full">
              <KeywordMap />
            </div>
          </section>

          <section className="grid grid-cols-3 gap-x-2 gap-y-2">
            <ChatbotFlow />
            <ChatbotUsage />
            <ErrorTypes />
          </section>

          <section className="grid grid-cols-3 gap-x-2 gap-y-2">
            <ModelToken />
            <ModelResponse />
            <ChatRoom />
          </section>

          <MonthlyUsage />
        </div>
      </section>
    </section>
  );
}
