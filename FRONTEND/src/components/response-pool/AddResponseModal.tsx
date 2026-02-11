import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface AddResponseModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function AddResponseModal({ open, onOpenChange, onSuccess }: AddResponseModalProps) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [category, setCategory] = useState('');

  async function handleSubmit() {
    if (!question || !answer) return;

    setLoading(true);
    try {
      await api.createResponsePoolItem({
        question_text: question,
        answer_text: answer,
        context: category ? [category] : [],
      });
      
      toast({
        title: "Response Added",
        description: "The Q&A pair has been added to the response pool.",
      });
      
      setQuestion('');
      setAnswer('');
      setCategory('');
      onOpenChange(false);
      onSuccess();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to add response. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add New Response</DialogTitle>
          <DialogDescription>
            Add a new Q&A pair to help the AI apply for programs more accurately.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="question">Question</Label>
            <Input
              id="question"
              placeholder="e.g., What are your traffic sources?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="answer">Answer</Label>
            <Textarea
              id="answer"
              placeholder="Provide a detailed answer..."
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              rows={4}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="category">Category / Context (Optional)</Label>
            <Input
              id="category"
              placeholder="e.g., SaaS, Retail, SEO"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!question || !answer || loading}>
            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Save Response
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
