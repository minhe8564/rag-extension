import ChatInput from '@/shared/components/chat/ChatInput';
import ChatMessageItem from '@/shared/components/chat/message/ChatMessageItem';
import ChatEmptyState from '@/shared/components/chat/layout/ChatEmptyState';
import { useChatLogic } from '@/shared/hooks/useChatLogic';
import { useChatScroll } from '@/shared/hooks/useChatScroll';

type ChatBrand = 'hebees' | 'retina';

interface TextChatProps {
  brand: ChatBrand;
}

export default function TextChatBase({ brand }: TextChatProps) {
  const {
    list,
    mode,
    setMode,
    initialLoading,
    awaitingAssistant,
    thinkingSubtitle,
    editingIdx,
    editingDraft,
    currentSessionNo,
    handleSend,
    startReask,
    cancelReask,
    submitReask,
    setList,
  } = useChatLogic();

  const { scrollRef, bottomRef, historyLoading } = useChatScroll({
    currentSessionNo,
    list,
    setList,
  });

  if (initialLoading) {
    return (
      <section className="flex flex-col min-h-[calc(100vh-82px)]">
        <div className="flex-1 flex items-center justify-center px-4">
          <div className="bg-gray-100 px-4 py-3 rounded-2xl shadow-sm flex items-center gap-2">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.2s]" />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.1s]" />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="flex min-h-[calc(100vh-82px)] flex-col">
      {list.length > 0 ? (
        <>
          <div
            ref={scrollRef}
            className="relative flex-1 min-h-0 w-full flex justify-center overflow-y-auto no-scrollbar"
          >
            <div className="w-full h-full max-w-[75%] space-y-10 px-12 py-4">
              {historyLoading && (
                <div className="flex justify-center py-3">
                  <div className="bg-gray-100 px-4 py-2 rounded-2xl shadow-sm flex items-center gap-2">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.2s]" />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.1s]" />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  </div>
                </div>
              )}

              {list.map((m, i) => (
                <ChatMessageItem
                  key={`${m.messageNo ?? 'pending'}-${i}`}
                  msg={m}
                  index={i}
                  currentSessionNo={currentSessionNo}
                  isEditing={m.role === 'user' && editingIdx === i}
                  editingDraft={editingDraft}
                  onStartReask={startReask}
                  onCancelReask={cancelReask}
                  onSubmitReask={submitReask}
                  isPendingAssistant={awaitingAssistant && m.role === 'assistant' && !m.content}
                  pendingSubtitle={thinkingSubtitle}
                  brand={brand}
                  enableDocuments={mode === 'rag'}
                />
              ))}

              <div ref={bottomRef} className="h-6" />
            </div>
          </div>

          <div className="sticky bottom-0 w-full flex justify-center">
            <div className="w-full max-w-[75%]">
              <ChatInput
                onSend={handleSend}
                variant={brand}
                mode={mode}
                onChangeMode={setMode}
                watch={list.length}
              />
            </div>
          </div>
        </>
      ) : (
        <div className="flex-1 flex items-center justify-center ">
          <div className="w-full max-w-[75%] flex flex-col items-center gap-4 text-center">
            <ChatEmptyState onSelectPrompt={handleSend} />
            <div className="w-full">
              <div className="bg-white pb-4">
                <ChatInput
                  onSend={handleSend}
                  variant={brand}
                  mode={mode}
                  onChangeMode={setMode}
                  watch={list.length}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
