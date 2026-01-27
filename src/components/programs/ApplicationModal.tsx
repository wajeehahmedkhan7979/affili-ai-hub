import { useState, useEffect } from 'react';
import { Program, ResponsePoolItem } from '@/lib/mock-data';
import { api } from '@/lib/api';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Loader2, Sparkles, Clock, CheckCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface ApplicationModalProps {
  program: Program | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ApplicationQuestion {
  id: string;
  question: string;
  suggestedAnswer: string;
  confidence: number;
}

export function ApplicationModal({ program, open, onOpenChange }: ApplicationModalProps) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [autoApprove, setAutoApprove] = useState(true);
  const [approvalHours, setApprovalHours] = useState(24);
  const [questions, setQuestions] = useState<ApplicationQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});

  useEffect(() => {
    if (open && program) {
      loadSuggestedAnswers();
      setSubmitted(false);
    }
  }, [open, program]);

  async function loadSuggestedAnswers() {
    setLoading(true);
    try {
      const responsePool = await api.getResponsePool();
      // Simulate AI matching questions to answers
      const mockQuestions: ApplicationQuestion[] = [
        {
          id: 'q1',
          question: 'Describe your traffic sources',
          suggestedAnswer: responsePool[0]?.answer_text || '',
          confidence: 0.92,
        },
        {
          id: 'q2', 
          question: 'How do you plan to promote our product?',
          suggestedAnswer: responsePool[1]?.answer_text || '',
          confidence: 0.88,
        },
        {
          id: 'q3',
          question: 'What is your website URL?',
          suggestedAnswer: responsePool[2]?.answer_text || '',
          confidence: 0.95,
        },
      ];
      setQuestions(mockQuestions);
      // Pre-fill answers
      const initialAnswers: Record<string, string> = {};
      mockQuestions.forEach(q => {
        initialAnswers[q.id] = q.suggestedAnswer;
      });
      setAnswers(initialAnswers);
    } catch (error) {
      console.error('Failed to load suggested answers:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit() {
    if (!program) return;
    
    setSubmitting(true);
    try {
      await api.createApplication(program.id, Object.values(answers));
      setSubmitted(true);
      toast({
        title: "Application Submitted",
        description: `Your application for ${program.name} has been submitted successfully.`,
      });
    } catch (error) {
      toast({
        title: "Submission Failed",
        description: "There was an error submitting your application. Please try again.",
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  }

  if (!program) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary font-semibold">
              {program.name.charAt(0)}
            </div>
            <div>
              <span>Apply to {program.name}</span>
              <Badge variant="outline" className="ml-2">{program.network}</Badge>
            </div>
          </DialogTitle>
          <DialogDescription>
            Review and customize the AI-suggested answers before submitting your application.
          </DialogDescription>
        </DialogHeader>

        {submitted ? (
          <div className="py-12 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-500/10">
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">Application Submitted!</h3>
            <p className="text-muted-foreground mb-6">
              Your application is now pending approval. 
              {autoApprove && ` It will be auto-approved in ${approvalHours} hours if not reviewed.`}
            </p>
            <Button onClick={() => onOpenChange(false)}>Close</Button>
          </div>
        ) : loading ? (
          <div className="py-12 flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-muted-foreground">Loading AI suggestions...</p>
          </div>
        ) : (
          <>
            <div className="space-y-6 py-4">
              {questions.map((q) => (
                <div key={q.id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">{q.question}</Label>
                    <div className="flex items-center gap-1">
                      <Sparkles className="h-3 w-3 text-primary" />
                      <span className="text-xs text-muted-foreground">
                        {Math.round(q.confidence * 100)}% confidence
                      </span>
                    </div>
                  </div>
                  <Textarea
                    value={answers[q.id] || ''}
                    onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                    rows={3}
                    className="resize-none"
                  />
                </div>
              ))}

              {/* Approval Settings */}
              <div className="rounded-lg border border-border bg-muted/50 p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label className="text-sm font-medium">Auto-approve on timeout</Label>
                    <p className="text-xs text-muted-foreground">
                      Automatically approve if not reviewed
                    </p>
                  </div>
                  <Switch checked={autoApprove} onCheckedChange={setAutoApprove} />
                </div>
                {autoApprove && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock className="h-4 w-4" />
                    <span>Auto-approve after {approvalHours} hours</span>
                  </div>
                )}
              </div>
            </div>

            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button onClick={handleSubmit} disabled={submitting}>
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  'Submit Application'
                )}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
