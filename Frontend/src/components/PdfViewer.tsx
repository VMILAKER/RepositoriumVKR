import { Viewer, Worker, RenderPageProps  } from '@react-pdf-viewer/core';

import '@react-pdf-viewer/core/lib/styles/index.css';

const renderPage = (props: RenderPageProps) => {
    return (
        <>
            {props.canvasLayer.children}
            <div style={{ userSelect: 'none' }}>
                {props.textLayer.children}
            </div>
            {props.annotationLayer.children}
        </>
    );
};

const PdfViewer = () => {
   const receivedValue = localStorage.getItem("sharedValue");
   localStorage.clear()
   return (
            <div style={{
                border: '1px solid rgba(0, 0, 0, 0.3)',
                flex: 1,
                overflow: 'hidden',

            }}>
                <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.4.120/build/pdf.worker.min.js">
                    <Viewer 
                        fileUrl={`http://url/${receivedValue}`}
                        renderPage={renderPage}
                    />
                </Worker>
            </div>
   );
};

export {PdfViewer};

