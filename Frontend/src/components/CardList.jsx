import { useEffect, useState } from 'react'
import {List, Card, Spin, Collapse, InputNumber} from 'antd'



function outputCardList(param, isLoad) {
    const [filterNumber, setFilterNumber] = useState(0)
    
    const handleChangeFilter_top = (event) => {
        if ((!filterNumber) || (filterNumber > param.length)) {
                setFilterNumber(param.length)
        }
        else {
            setFilterNumber(event)
        }
    };

    
    else if (filterNumber <= 1) {
        setFilterNumber(Math.round(param.length*filterNumber))
        }
    const handleChangeFilter_percent = (event) => {
      setFilterNumber(event/100)
    };

    const tag_array = (param) => {
        let final_tag = []
        for (let i in param) {
            final_tag.push(param[i].tag_name)
        }
        return final_tag.join(', ')
    };


    try {
        if (isLoad) {
            return (<div className='flex'>
                <p className='text-[#242424] mx-2'>Loading</p><Spin size='large'/>
            </div>
            )
        }
        else {
            if ((!filter_number) || (filter_number > param.length)) {
                filter_number = param.length
                }
            else if (filter_number <= 1) {
                filter_number = Math.round(param.length*filter_number)
                }
            return (
                <div className="place-items-center m-2 text-center">
                    <div>
                        <p className='mb-2'>Количество результатов: {filter_number}</p>            
                    </div>
                    <Collapse className='w-100 bg-black' size='small' items={[{label: 'Фильтр', children: <ul className='text-left'><li className='mb-2'>Топ-{filter_number} записей: {<InputNumber name='top' min={1} max={param.length} onChange={handleChangeFilter_top}/>}</li><li>Процент от всех записей, %: {<InputNumber name='percent' min={1} max={100} onChange={handleChangeFilter_percent}/>} </li></ul>}]}/>
                    <List>
                        {param.length >0 && param.slice(0, filter_number).map((item) => <div key = {item.id} className='w-170 my-4 text-left text-wrap'>
                        <Card component='span' title={`ВКР_${item?.type_of_qualification}`}>
                        <p className='my-2'><span className='font-bold'>Тема: </span>{item?.theme}</p>
                        <div className='flex items-center my-2'><span className='font-bold'>Руководитель: </span><Collapse className='w-100' size='small' items={[{label:item?.supervisor_gqw.name, children: <ul><li>Место работы: {item?.supervisor_gqw.department}</li><li>Учёная степень: {item?.supervisor_gqw.degree}</li></ul>}]}/></div>
                        <p className='my-2'><span className='font-bold'>Уровень образования: </span>{item?.type_of_qualification}</p>
                        <p className='my-2 text-justify'><span className='font-bold'>Аннотация: </span>{item?.abstract}</p>
                        <p className='my-2'><span className='font-bold'>Ссылка на аннотацию: </span><a className='text-justify' href={`http://localhost:5173/pdf_docs/${item?.reference}`} target="_blank" >{item?.reference}</a></p>
                        <p className='my-2'><span className='font-bold'>Тэги: </span>{tag_array(item?.tag_gqw)}</p>
                        </Card>
                        </div>)}
                    </List>
                </div>
            )
            }
        }
        catch (err) {
        return (
                <p id='noData' className='text-center text-xl'>Sorry, there is no data available </p>
            )
        }
};


export default outputCardList