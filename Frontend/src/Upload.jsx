import { useEffect, useState } from 'react'
import axios from 'axios'
import { Button, Form, Input, Select, Space,List, Card, Spin, Switch, Collapse, Upload, message} from 'antd';
import { UploadOutlined } from '@ant-design/icons';

function Upload() {
    const props = {
      name: 'file',
      url: 'http://localhost:5173/public/pdf_docs/',
      headers: {
        authorization: 'authorization-text',
      },
      onChange(info) {
        if (info.file.name.includes('.pdf')) {
          if (info.file.status !== 'uploading') {
          console.log(info.file, info.fileList);
          }
          if (info.file.status === 'done') {
            message.success(`${info.file.name} file uploaded successfully`);
          } else if (info.file.status === 'error') {
            message.error(`${info.file.name} file upload failed.`);
          }
        }
        else {
          message.error(`file should be .pdf`)
          alert(`file should be .pdf`)
        }
      },
    };
}