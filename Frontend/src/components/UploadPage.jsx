import { useEffect, useState } from 'react'
import axios from 'axios'
import * as util from './Utilities.jsx';
import { UploadOutlined } from '@ant-design/icons';
import { Button, Form, Input, Select, Space, Upload,  Checkbox, message} from 'antd';


const formUpload = {
  theme: '',
  supervisor: '', 
  type_of_qualification: '',
//   abstract: '',
  reference: '',
  tags: ''
};

const layout = {
  labelCol: { span: 8 },
  wrapperCol: { span: 16 },
};

const tailLayout = {
  wrapperCol: { offset: 6, span: 12 },
};

function UploadVKR() {
    const [getSupervisors, setSupervisors] = useState([])
    const [getReferences, setReferences] = useState([])
    const [getDepartments, setDepartments] = useState([])
    const [getDegrees, setDegrees] = useState([])
    const [getThemes, setThemes] = useState([])
    const [getTags, setTags] = useState([])
    const [dataUpload, setDataUpload] = useState(formUpload);
    const [selectedFile, setSelectedFile] = useState(null);
    const [isChecked, setChecked] = useState(false);
    const [messageApi, contextHolder] = message.useMessage();
    const [form] = Form.useForm();
    const { Option } = Select;

    const url = "http://10.6.41.116:8001/repositorium"

    const messageSystem = (type_message, params, key) => {
        messageApi.open({
        key,
        type: type_message,
        content: params,
        duration: 4,
        });
    };

    const props = {
        maxCount: 1,
        multiple: false,
        beforeUpload: info => {
        const isPdf = info.type === 'application/pdf'
        if (!isPdf) {
            messageSystem('error', `${info.name} is not a pdf file`, 'notPdf')
            return isPdf || Upload.LIST_IGNORE
        }
        else {
            if (!(getReferences.includes(info.name, 0))) {
            setSelectedFile(info)
            setDataUpload({...dataUpload, reference: info.name})
            return false
            }
            else {
            messageSystem('error', `${info.name} already exists`, 'pdfExists')
            }
        }
        }
    };

    const onResetUpload = () => {
        form.resetFields()
        setDataUpload(formUpload)
    };
    
    const SelectChange_qualification_upload = (event) => {
        setDataUpload({...dataUpload, type_of_qualification: event})
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

    const SelectChange_tags_upload = (event) => {
        let tag_list = []
        tag_list.push(event)
        setDataUpload({...dataUpload, tags:tag_list.join(',')})
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
                setThemes(getOptions[0])
                setReferences(getOptions[1])
                setDepartments(getOptions[2])
                setSupervisors(getOptions[3])
                setDegrees(getOptions[4])
                setTags(getOptions[5])
            }
        })
        }
        catch(err) {
            console.error('Error', err)
            alert(`Something wrong: ${err}`)
        }
    };

    const uploadData = async(dataUpload, url_) => {
        const formData = new FormData()
        formData.append('file', selectedFile)
        try {
            let empty_fields =0 
            for (let i in dataUpload) {
                if (!(dataUpload[i])) {
                    empty_fields++
                }
            }
            if (empty_fields == 0) {
                if (!(getThemes.includes(dataUpload?.theme, 0))) {
                    messageSystem('loading', 'Download in progress', 'loadingData')
                    await axios.post(`${url_}/create_file`, formData)
                    await axios.post(`${url_}/post`, dataUpload)
                    messageSystem('success', `Data is downloaded!`, 'uploadSuccess')
                    fetchPrior(url)
                }
                else {
                    message.destroy('loadingData')
                    messageSystem('error', `${dataUpload?.theme} already exists!`, 'themeExists')
                }
            }
            else {
                alert("Can't be transferred because fields is empty!")
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
        <div className="flex flex-col pt-2 place-items-center bg-red-400">
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
                    <Form.Item name="theme_upload" label="Тема">
                        <Input name="theme" placeholder='Тема ВКР' onChange = {handleChange_upload} allowClear/>
                    </Form.Item>
                    <Form.Item name="type_of_qualification" label="Квалификация">
                        <Select
                        name='quallification'
                        placeholder="Выберите квалификацию"
                        onChange = {SelectChange_qualification_upload}
                        allowClear
                        >
                        <Option value="Бакалавриат">Бакалавриат</Option>
                        <Option value="Магистратура">Магистратура</Option>
                        </Select>
                    </Form.Item>
                    <Form.Item>
                        <Checkbox onChange={() => {setChecked(!isChecked)}}>Руководителя нет в списке</Checkbox>
                        {onChange_checkboxSupervisor()}
                    </Form.Item>
                    {/* <Form.Item name="abstract" label="Аннотация">
                        <Input name="abstract" placeholder='Введите аннотацию' onChange = {handleChange_upload} allowClear/>
                    </Form.Item> */}
                    <Form.Item name='reference' label='Файл аннотации (.pdf)'>
                        <Upload {...props}>
                        <Button icon={<UploadOutlined/>} >Click to upload</Button>
                        </Upload>
                    </Form.Item>
                    <Form.Item name="tags" label="Тэги">
                        <Select name='tags'
                        showSearch
                        mode='tags'
                        placeholder="Выберите или введите место работы"
                        onChange={SelectChange_tags_upload}
                        options={getTags}
                        optionFilterProp='label'
                        filterSort = {(a, b) => ((a?.label ?? '').toLowerCase()).localeCompare((b?.label ?? '').toLowerCase())}
                        allowClear
                    />
                    </Form.Item>
                    <Form.Item {...tailLayout}>
                        <Space>
                        <Button onClick = {() =>{
                            uploadData(dataUpload, url)
                            console.log("transfer",dataUpload)
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