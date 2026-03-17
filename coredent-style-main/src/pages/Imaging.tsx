/**
 * Imaging Page
 * Digital X-ray, DICOM viewer, annotations
 */

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { 
  Search, 
  Plus, 
  Image, 
  Upload, 
  Eye,
  Share2,
  Trash2,
  Download,
  ZoomIn,
  ZoomOut,
  RotateCw
} from "lucide-react";

export default function Imaging() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  const studies = [
    { id: "1", patient: "John Smith", type: "X-Ray (PA)", date: "Feb 12, 2026", teeth: "Full Mouth", status: "Completed" },
    { id: "2", patient: "Jane Doe", type: "X-Ray (Bitewing)", date: "Feb 10, 2026", teeth: "#15-18", status: "Completed" },
    { id: "3", patient: "Bob Johnson", type: "Panoramic", date: "Feb 8, 2026", teeth: "Full", status: "Completed" },
    { id: "4", patient: "Mary Wilson", type: "CBCT", date: "Feb 5, 2026", teeth: "#3", status: "Pending Review" },
  ];

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Imaging</h1>
          <p className="text-muted-foreground">Digital X-ray and DICOM image management</p>
        </div>
        <Button>
          <Upload className="mr-2 h-4 w-4" />
          Upload Image
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Studies</CardTitle>
            <Image className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,245</div>
            <p className="text-xs text-muted-foreground">this year</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Month</CardTitle>
            <Image className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">45</div>
            <p className="text-xs text-muted-foreground">new studies</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
            <Eye className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-500">3</div>
            <p className="text-xs text-muted-foreground">need attention</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Shared</CardTitle>
            <Share2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div>
            <p className="text-xs text-muted-foreground">with specialists</p>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search by patient or study type..." 
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="studies" className="space-y-4">
        <TabsList>
          <TabsTrigger value="studies">Studies</TabsTrigger>
          <TabsTrigger value="viewer">Image Viewer</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
        </TabsList>

        <TabsContent value="studies">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Patient</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Teeth</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {studies.map((study) => (
                    <TableRow key={study.id}>
                      <TableCell className="font-medium">{study.patient}</TableCell>
                      <TableCell><Badge variant="outline">{study.type}</Badge></TableCell>
                      <TableCell>{study.date}</TableCell>
                      <TableCell>{study.teeth}</TableCell>
                      <TableCell>
                        <Badge className={study.status === 'Completed' ? 'bg-green-500' : 'bg-yellow-500'}>
                          {study.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button size="sm" variant="ghost" onClick={() => setSelectedImage(study.id)}>
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button size="sm" variant="ghost">
                            <Share2 className="h-4 w-4" />
                          </Button>
                          <Button size="sm" variant="ghost">
                            <Download className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="viewer">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Image Viewer</CardTitle>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline">
                    <ZoomIn className="h-4 w-4 mr-1" />
                    Zoom In
                  </Button>
                  <Button size="sm" variant="outline">
                    <ZoomOut className="h-4 w-4 mr-1" />
                    Zoom Out
                  </Button>
                  <Button size="sm" variant="outline">
                    <RotateCw className="h-4 w-4 mr-1" />
                    Rotate
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-96 bg-gray-100 rounded-lg flex items-center justify-center">
                {selectedImage ? (
                  <p className="text-muted-foreground">Viewing study {selectedImage}</p>
                ) : (
                  <p className="text-muted-foreground">Select an image to view</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="templates">
          <Card>
            <CardHeader>
              <CardTitle>Image Templates</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium">Full Mouth Series</h4>
                  <p className="text-sm text-muted-foreground">18 X-rays</p>
                </div>
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium">Bitewing Series</h4>
                  <p className="text-sm text-muted-foreground">4 X-rays</p>
                </div>
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium">PA + Bitewing</h4>
                  <p className="text-sm text-muted-foreground">6 X-rays</p>
                </div>
              </div>
              <Button variant="outline" className="mt-4">
                <Plus className="mr-2 h-4 w-4" />
                Add Template
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
