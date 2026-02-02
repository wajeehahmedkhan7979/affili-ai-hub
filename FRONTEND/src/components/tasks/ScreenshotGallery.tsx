import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { useState } from "react";

interface ScreenshotGalleryProps {
  screenshots: {
    before?: string;
    filled?: string;
    after?: string;
  } | null;
  taskId: string;
}

export function ScreenshotGallery({ screenshots, taskId }: ScreenshotGalleryProps) {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  if (!screenshots || Object.keys(screenshots).length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Screenshots</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            No screenshots available
          </p>
        </CardContent>
      </Card>
    );
  }

  // Construct full URLs for screenshots
  const baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  
  const images: Array<{ label: string; url: string | null }> = [
    { label: "Before", url: screenshots.before },
    { label: "Filled", url: screenshots.filled },
    { label: "After", url: screenshots.after },
  ].filter((img) => img.url);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Screenshots</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {images.map(({ label, url }) => (
            <Dialog key={label}>
              <DialogTrigger asChild>
                <div
                  className="cursor-pointer border rounded-lg overflow-hidden hover:shadow-lg transition-shadow"
                  onClick={() => setSelectedImage(url)}
                >
                  <div className="bg-slate-100 p-2 text-center text-sm font-medium">
                    {label}
                  </div>
                  <img
                    src={url || ""}
                    alt={`${label} screenshot`}
                    className="w-full h-48 object-cover"
                  />
                </div>
              </DialogTrigger>
              <DialogContent className="max-w-4xl">
                <img
                  src={selectedImage || ""}
                  alt={`${label} screenshot (expanded)`}
                  className="w-full h-auto"
                />
              </DialogContent>
            </Dialog>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
