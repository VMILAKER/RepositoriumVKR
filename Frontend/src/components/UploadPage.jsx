import { useEffect, useState } from 'react'
import axios from 'axios'
import * as util from './Utilities.jsx';
import { UploadOutlined } from '@ant-design/icons';
import { Button, Form, Input, Select, Space, Upload,  Checkbox, message} from 'antd';


const formUpload = {
  supervisor: '', 
  reference: ''
};

const layout = {
  labelCol: { span: 8 },
  wrapperCol: { span: 16 },
};

const tailLayout = {
  wrapperCol: { offset: 6, span: 12 },
};

const stylesShared = {
  label:{
      color:'#ffffff',
  }
};

function UploadVKR() {
    const [getSupervisors, setSupervisors] = useState([])
    const [getReferences, setReferences] = useState([])
    const [getDepartments, setDepartments] = useState([])
    const [getDegrees, setDegrees] = useState([])
    const [dataUpload, setDataUpload] = useState(formUpload);
    const [selectedFile, setSelectedFile] = useState(null);
    const [isChecked, setChecked] = useState(false);
    const [messageApi, contextHolder] = message.useMessage();
    const [form] = Form.useForm();
    const { Option } = Select;

    const url = "http://url/repository"

    const messageSystem = (type_message, params, time) => {
        messageApi.open({
            type: type_message,
            content: params,
            duration: time,
            maxCount:1,
        });
    };

    const props = {
        maxCount: 1,
        multiple: false,
        beforeUpload: info => {
        const isPdf = info.type === 'application/pdf'
        if (!isPdf) {
            messageSystem('error', `${info.name} не является pdf файлом`, 4)
            return isPdf || Upload.LIST_IGNORE
        }
        else {
            if (!(getReferences.includes(info.name, 0))) {
                setSelectedFile(info)
                setDataUpload({...dataUpload, reference: info.name})
                return false
            }
            else {
                messageSystem('error', `${info.name} уже существует`, 4)
                return isPdf || Upload.LIST_IGNORE
            }
        }
        }
    };

    const onResetUpload = () => {
        form.resetFields()
        setDataUpload(formUpload)
    };

    const SelectChange_supervisor_upload = (event) => {
        setDataUpload({...dataUpload, supervisor: event})
    };

    const SelectChange_department_upload = (event) => {
        setDataUpload({...dataUpload, department:event[0]})
    };

    const SelectChange_degree_upload = (event) => {
        setDataUpload({...dataUpload, degree:event[0]})
    };

    const handleChange_upload = (event) => {
        setDataUpload({...dataUpload, [event.target.name]: event.target.value})
    };

    const handleSubmit = async event => {
        event.preventDefault()
    };
    
    const fetchPrior = async(url_) => {
        try {
            let getOptions = [];
            await axios.get(`${url_}/preloaded_data`).then(r => {
                getOptions = r.data
                if (getOptions.length > 0) {
                    setReferences(getOptions[1])
                    setDepartments(getOptions[2])
                    setSupervisors(getOptions[3])
                    setDegrees(getOptions[4])
                }
            })
        }
        catch(err) {
            console.error('Error', err)
            alert(`Something wrong: ${err}`)
        }
    };

    const uploadData = async(upload_dict, url_) => {
        const formData = new FormData()
        formData.append('file', selectedFile)
        try {
            let empty_fields =0           
            for (let value of Object.values(upload_dict)) {
                if (!value) {
                    empty_fields++
                }
            }
            if (empty_fields == 0) {
                    messageSystem('loading', 'Добавление', 15)
                    await axios.post(`${url_}/create_file`, formData).then(r => {
                        let responce = r.data
                        if (responce === 'The file is uploaded') {
                            axios.post(`${url_}/post`, upload_dict)
                            messageSystem('success', `ВКР загружена!`, 4)
                            fetchPrior(url)
                        }
                        else {
                            message.destroy('loadingData')
                            messageSystem('error', `${responce} уже существует`, 4)
                        }
                    })
            }
            else {
                messageSystem('error', "Не все поля заполнены!", 4)
            }
        }
        catch(err) {
            console.error('Error', err)
            alert(`Something wrong: ${err}`)
        }
    };


    function onChange_checkboxSupervisor() {
        if (!isChecked) {
            return (
                <Select name='supervisor'
                    showSearch
                    placeholder="Выберите научного руководителя"
                    onChange={SelectChange_supervisor_upload}
                    options={getSupervisors}
                    optionFilterProp='label'
                    filterSort = {(a, b) => ((a?.label ?? '').toLowerCase()).localeCompare((b?.label ?? '').toLowerCase())}
                    allowClear
                />
            )
        }
        else {
            return (
                <div className='ml-6'>
                    <Input className='my-1' name="supervisor" placeholder='Фамилия И.О. научного руководителя' onChange = {handleChange_upload} allowClear/>
                    <Select name='department'
                        showSearch
                        mode='tags'
                        placeholder="Выберите или введите место работы"
                        onChange={SelectChange_department_upload}
                        options={getDepartments}
                        optionFilterProp='label'
                        filterSort = {(a, b) => ((a?.label ?? '').toLowerCase()).localeCompare((b?.label ?? '').toLowerCase())}
                        allowClear
                    />
                    <div className="my-1">
                    <Select name='degree' 
                        showSearch
                        mode='tags'
                        placeholder="Выберите или введите учёную степень"
                        onChange={SelectChange_degree_upload}
                        options={getDegrees}
                        optionFilterProp='label'
                        filterSort = {(a, b) => ((a?.label ?? '').toLowerCase()).localeCompare((b?.label ?? '').toLowerCase())}
                        allowClear
                    />
                    </div>
                </div>
            )
        }
    };

    useEffect(() => {
        fetchPrior(url)
    }, [url]);
    
    return(
        <div className="flex flex-col pt-2 place-items-center">
            {contextHolder}
            <div className='flex w-290 bg-slate-500 p-6 m-2 rounded-md text-wrap'>
                <div className='w-180'>
                    <Form
                        {...layout}
                        form={form}
                        layout='vertical'
                        name="upload_data"
                        onSubmitCapture={handleSubmit}
                        autoComplete='off'
                    >
                    <Form.Item>
                        <Checkbox onChange={() => {setChecked(!isChecked)}}><span className='text-white'>Руководителя нет в списке</span></Checkbox>
                        {onChange_checkboxSupervisor()}
                    </Form.Item>
                    <Form.Item name='reference' label={<span className='text-white'>Файл ВКР (.pdf)</span>} styles={stylesShared}>
                        <Upload {...props}>
                        <Button icon={<UploadOutlined/>} >Click to upload</Button>
                        </Upload>
                    </Form.Item>  
                    <Form.Item {...tailLayout}>
                        <Space>
                        <Button onClick = {() =>{
                            uploadData(dataUpload, url)
                        }
                            } type="primary" htmlType="submit">
                            Загрузить
                        </Button>
                        <Button htmlType="button" onClick={onResetUpload}>
                            Сбросить
                        </Button>
                        </Space>
                    </Form.Item>
                    </Form>
                </div>
            {util.noteUpload()}
            </div>
        </div>
    )
}

export {UploadVKR};