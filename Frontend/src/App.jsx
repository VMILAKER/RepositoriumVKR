import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { App_main} from './components/SearchPage.jsx';
import {UploadVKR} from './components/UploadPage.jsx'
import { PdfViewer } from './components/PdfViewer.tsx';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App_main/>} />
        <Route path="/upload" element={<UploadVKR/>} />
        <Route path="/pdf_viewer" element={<PdfViewer/>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;