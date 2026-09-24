import { useEffect, useState } from 'react'
import axios from 'axios'
import * as util from './Utilities.jsx';
import { UploadOutlined } from '@ant-design/icons';
import { Button, Form, Input, Select, Space, Upload,  Checkbox, message} from 'antd';


function UploadVKR() {
    const [getSupervisors, setSupervisors] = useState([])
    const [getReferences, setReferences] = useState([])
    const [getDepartments, setDepartments] = useState([])
    const [getDegrees, setDegrees] = useState([])
    const [dataUpload, setDataUpload] = useState(util.uploadForm);
    const [selectedFile, setSelectedFile] = useState(null);
    const [isChecked, setChecked] = useState(false);
    const [getApiKey, SetApiKey] = useState(util.uploadHeaders);
    const [messageApi, contextHolder] = message.useMessage();
    const [form] = Form.useForm();

    const backend_url = import.meta.env.VITE_BACKEND_URL;
    const api_key = import.meta.env.VITE_API_KEY;
    const headers = { "API_Key": api_key };
    

    
    const messageSystem = (key, type_message, params, time) => {
        messageApi.open({
            key: key, 
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
            messageSystem('errorKey', 'error', `${info.name} не является pdf файлом`, 4)
            return isPdf || Upload.LIST_IGNORE
        }
        else {
            if (!(getReferences.includes(info.name, 0))) {
                setSelectedFile(info)
                return false
            }
            else {
                messageSystem('errorKey', 'error', `${info.name} уже существует`, 4)
                return isPdf || Upload.LIST_IGNORE
            }
        }
        }
    };

    const onResetUpload = () => {
        form.resetFields()
        setDataUpload(util.formUpload)
    };

    const SelectChange_supervisor_upload = (event) => {
        if (!(event === 'No data') ){
            setDataUpload({...dataUpload, supervisor: event})
        }
        else {
            messageSystem('errorSupervisor', 'error', 'Введите руководителя ВКР', 4)
        }
        
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

    const handleApiKey = (event) => {
        SetApiKey({...getApiKey, [event.target.name]: event.target.value})
        
    }
    const handleSubmit = async event => {
        event.preventDefault()
    };
    
    const fetchPrior = async(url_, headers) => {
        try {
            let getOptions = [];
            await axios.get(`${url_}/get_preloaded_data`, {headers}).then(r => {
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

    const uploadData = async(upload_dict, url_, headers) => {
        const formData = new FormData()
        formData.append('file', selectedFile)
        
        try {
            if (!Object.values(upload_dict).some(value => value === null || value === undefined || value === "") && selectedFile) {
                if (api_key === getApiKey['API_Key']) {
                    messageSystem('loadKey', 'loading', 'Добавление', 120)

                    await axios.post(`${url_}/upload_vkr`, formData, {params: {'data': JSON.stringify(upload_dict)}, headers:headers}).then(r => {
                        const response = r.data
                        if (response === 'The file is uploaded') {
                            messageApi.destroy('loadKey',)
                            messageSystem('successKey', 'success', `ВКР загружена!`, 4)
                            fetchPrior(url_, headers)
                        }
                        else {
                            messageApi.destroy('loadKey')
                            messageSystem('errorKey', 'error', `${response} уже существует`, 4)
                        }
                    })
                }
                else {
                    messageSystem('errorApi', 'error', 'Неверный API-ключ!', 4)
                }
            }
            else {
                messageSystem('errorKey', 'error', "Не все поля заполнены!", 4)
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
        fetchPrior(backend_url, headers)
    }, [backend_url]);
    
    return(
        <div className="flex flex-col pt-2 place-items-center">
            {contextHolder}
            <div className='flex w-290 bg-slate-500 p-6 m-2 rounded-md text-wrap'>
                <div className='w-180'>
                    <Form
                        {...util.layout}
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
                    <Form.Item>
                        <Input className='my-1' name="API_Key" placeholder='Введите API-ключ' onChange = {handleApiKey} allowClear/>
                    </Form.Item>
                    <Form.Item name='reference' label={<span className='text-white'>Файл ВКР (.pdf)</span>} styles={util.stylesShared}>
                        <Upload {...props}>
                        <Button icon={<UploadOutlined/>} >Click to upload</Button>
                        </Upload>
                    </Form.Item>  
                    <Form.Item {...util.tailLayout}>
                        <Space>
                        <Button onClick = {() =>{
                            uploadData(dataUpload, backend_url, getApiKey)
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