import { Viewer, Worker } from "@react-pdf-viewer/core";
import { toolbarPlugin } from "@react-pdf-viewer/toolbar";
import "@react-pdf-viewer/toolbar/lib/styles/index.css";
import "@react-pdf-viewer/core/lib/styles/index.css";
import { useEffect, useState } from "react";
import axios from "axios";

function PdfViewer() {
  const filename = localStorage.getItem("filename");
  const bucketType = localStorage.getItem("bucket_type");

  const url = import.meta.env.VITE_BACKEND_URL;
  const apiKey = import.meta.env.VITE_API_KEY;
  const headers = { "API_Key": apiKey };

  const [pdfUrl, setPdfUrl] = useState(null);
  const [error, setError] = useState(null);

  const toolbarPluginInstance = toolbarPlugin()
  const { Toolbar } = toolbarPluginInstance;

  useEffect(() => {
    let objectUrl = null;

    const fetchPdf = async () => {
      try {
        const response = await axios.get(`${url}/get_file/${filename}`, {
          params: { filename, bucket_type: bucketType },
          headers,
          responseType: "blob",
        });

        objectUrl = URL.createObjectURL(response.data);
        setPdfUrl(objectUrl);
        localStorage.clear()

      } catch (err) {
        console.error("Error", err);
        setError("Не удалось загрузить PDF");
      }
    };

    if (filename && bucketType) {
      fetchPdf();
    } 
    else {
      setError("Отсутствуют параметры файла");
    }
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, []);
  
  useEffect(() => {
    const blockContext = (e) => e.preventDefault();
    const blockCopy = (e) => {
      if ((e.ctrlKey || e.metaKey) && (e.key === "c" || e.key === "C")) {
        e.preventDefault();
      }
      if ((e.ctrlKey || e.metaKey) && (e.key === "s" || e.key === "S")) {
        e.preventDefault();
      }
    };

    document.addEventListener("contextmenu", blockContext);
    document.addEventListener("keydown", blockCopy);

    return () => {
      document.removeEventListener("contextmenu", blockContext);
      document.removeEventListener("keydown", blockCopy);
    };
  }, []);

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center text-red-600">
        {error}
      </div>
    );
  }

  if (!pdfUrl) {
    return (
      <div className="flex h-screen items-center justify-center">Загрузка...</div>
    );
  }

  return (
    <div
      className="h-screen w-screen"
      style={{
        userSelect: "none",
        WebkitUserSelect: "none",
        MozUserSelect: "none",
        msUserSelect: "none",
      }}
    >
      <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.4.120/build/pdf.worker.min.js">
         <Toolbar>
          {(slots) => {
            const {
              CurrentPageInput,
              EnterFullScreen,
              GoToNextPage,
              GoToPreviousPage,
              NumberOfPages,
              ShowSearchPopover,
              Zoom,
              ZoomIn,
              ZoomOut,
            } = slots;

            return (
              <div
                style={{
                  alignItems: "center",
                  display: "flex",
                  width: "100%",
                }}
              >
                <div style={{ padding: "0px 2px" }}>
                  <ShowSearchPopover />
                </div>
                <div style={{ padding: "0px 2px" }}>
                  <ZoomOut />
                </div>
                <div style={{ padding: "0px 2px" }}>
                  <Zoom />
                </div>
                <div style={{ padding: "0px 2px" }}>
                  <ZoomIn />
                </div>
                <div style={{ padding: "0px 2px", marginLeft: "auto" }}>
                  <GoToPreviousPage />
                </div>
                <div style={{ padding: "0px 2px", width: "4rem" }}>
                  <CurrentPageInput />
                </div>
                <div style={{ padding: "0px 2px" }}>
                  / <NumberOfPages />
                </div>
                <div style={{ padding: "0px 2px" }}>
                  <GoToNextPage />
                </div>
                <div style={{ padding: "0px 2px", marginLeft: "auto" }}>
                  <EnterFullScreen />
                </div>
              </div>
            );
          }}
        </Toolbar>

        <Viewer fileUrl={pdfUrl} plugins={[toolbarPluginInstance]} />
      </Worker>
    </div>
  );
}

export { PdfViewer };
